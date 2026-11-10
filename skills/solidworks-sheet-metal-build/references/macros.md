# Sheet-metal macro templates

These are SolidWorks Basic `.swb` text macros. Run them through `solidworks-macro-fallback` (CRLF line endings, legacy `RunMacro`, verify after the run). Values are metres. Edit the `Const` block for each job. Each macro writes a log; read it after the run.

## Edge flanges on one opposite pair of edges

Find edges by geometry. `SelectByID2` with coordinates picked the wrong (outer-face) edge. The macro below matches edge end points in either order, within a tolerance.

Sketch frame from `InsertSketchForEdgeFlange`: the origin is the edge midpoint, x runs along the edge, y points in the flange direction. Profile height `H` = outer flange length − t (Material Inside).

```vb
Const PI As Double = 3.14159265358979
Const T As Double = 0.0015        ' thickness
Const RI As Double = 0.0015       ' inside bend radius
Const H As Double = 0.0485        ' outer flange length - T
Const L As Double = 0.2           ' profile length along the edge (see corner rules)
Const TOL As Double = 0.00001
Const LOGPATH As String = "C:\Project\Macros\edge_flange.log"

Dim swApp As Object
Dim Part As Object
Dim lf As Integer

Sub main()
    Set swApp = Application.SldWorks
    Set Part = swApp.ActiveDoc
    lf = FreeFile
    Open LOGPATH For Output As #lf
    On Error Resume Next

    Dim body As Object
    Dim bodies As Variant
    bodies = Part.GetBodies2(0, True)
    Set body = bodies(0)

    Dim e1 As Object, e2 As Object
    ' Edge end points (x1,y1,z1)-(x2,y2,z2) on the flange side of the base
    Set e1 = FindEdge(body, -0.15, -0.1, 0, -0.15, 0.1, 0)
    Set e2 = FindEdge(body, 0.15, -0.1, 0, 0.15, 0.1, 0)
    Print #lf, "edges found: "; Not e1 Is Nothing; Not e2 Is Nothing

    Dim s1 As Object, s2 As Object
    Set s1 = ProfileSketch(e1)
    Set s2 = ProfileSketch(e2)

    Dim edges(1) As Object, sks(1) As Object
    Set edges(0) = e1: Set edges(1) = e2
    Set sks(0) = s1: Set sks(1) = s2
    Dim vE As Variant, vS As Variant
    vE = edges: vS = sks                ' object arrays passed directly returned Nothing

    Dim f As Object
    ' 128 default relief, position 1 Material Inside, relief 1 rectangular, ratio 0.5
    Set f = Part.FeatureManager.InsertSheetMetalEdgeFlange2(vE, vS, 128, PI / 2, RI, 1, 0, 1, 0.5, 0, 0, 1, Nothing)
    If f Is Nothing Then
        Print #lf, "edge flange: Nothing "; Err.Description
    Else
        Print #lf, "edge flange: "; f.Name
    End If
    Part.EditRebuild3
    Close #lf
End Sub

Function ProfileSketch(edge As Object) As Object
    Dim sf As Object
    Set sf = Part.InsertSketchForEdgeFlange(edge, PI / 2, False)
    sf.Select2 False, 0                 ' returned sketch is not in edit mode
    Part.EditSketch
    Part.SketchManager.CreateCornerRectangle -L / 2, 0, 0, L / 2, H, 0
    Part.SketchManager.InsertSketch True
    Print #lf, "profile sketch: "; Err.Description
    Set ProfileSketch = sf
End Function

Function FindEdge(body As Object, x1 As Double, y1 As Double, z1 As Double, _
                  x2 As Double, y2 As Double, z2 As Double) As Object
    Dim es As Variant, i As Long, a As Variant, b As Variant
    es = body.GetEdges
    For i = 0 To UBound(es)
        a = es(i).GetStartVertex.GetPoint
        b = es(i).GetEndVertex.GetPoint
        If (Near(a, x1, y1, z1) And Near(b, x2, y2, z2)) Or _
           (Near(a, x2, y2, z2) And Near(b, x1, y1, z1)) Then
            Set FindEdge = es(i)
            Exit Function
        End If
    Next i
    Set FindEdge = Nothing
End Function

Function Near(p As Variant, x As Double, y As Double, z As Double) As Boolean
    Near = Abs(p(0) - x) < TOL And Abs(p(1) - y) < TOL And Abs(p(2) - z) < TOL
End Function
```

If `FindEdge` returns Nothing, log every edge's end points and pick the right pair from the log. Do not guess coordinates again.

## Custom K-factor on named bend features

```vb
Const K As Double = 0.44
Const LOGPATH As String = "C:\Project\Macros\kfactor.log"

Sub main()
    Dim swApp As Object, Part As Object, f As Object, d As Object, cba As Object
    Dim names As Variant, i As Long, lf As Integer
    Set swApp = Application.SldWorks
    Set Part = swApp.ActiveDoc
    lf = FreeFile
    Open LOGPATH For Output As #lf
    On Error Resume Next
    names = Array("Edge-Flange1", "Edge-Flange2")
    For i = 0 To UBound(names)
        Set f = Part.FeatureByName(names(i))
        Set d = f.GetDefinition
        d.AccessSelections Part, Nothing
        d.UseDefaultBendAllowance = False
        Set cba = d.GetCustomBendAllowance
        cba.Type = 2                    ' K-factor
        cba.KFactor = K
        d.SetCustomBendAllowance cba
        Print #lf, names(i); " modified: "; f.ModifyDefinition(d, Part, Nothing); " "; Err.Description
        Err.Clear
    Next i
    Part.EditRebuild3
    Close #lf
End Sub
```

## End-face probe (wall ends and corner gaps)

This lists planar faces whose normal is along X or Y and whose box is `t` thick in one in-plane direction. Those are the cut ends of walls and flanges. Use it to read wall end positions and butt-corner gaps.

```vb
Const T As Double = 0.0015
Const TOL As Double = 0.00002
Const LOGPATH As String = "C:\Project\Macros\end_faces.log"

Sub main()
    Dim swApp As Object, Part As Object, body As Object, fc As Object
    Dim bodies As Variant, faces As Variant, n As Variant, bx As Variant
    Dim i As Long, lf As Integer, dx As Double, dy As Double, dz As Double
    Set swApp = Application.SldWorks
    Set Part = swApp.ActiveDoc
    lf = FreeFile
    Open LOGPATH For Output As #lf
    On Error Resume Next
    bodies = Part.GetBodies2(0, True)
    Set body = bodies(0)
    faces = body.GetFaces
    For i = 0 To UBound(faces)
        Set fc = faces(i)
        If fc.GetSurface.IsPlane Then
            n = fc.Normal
            bx = fc.GetBox
            dx = Abs(bx(3) - bx(0)): dy = Abs(bx(4) - bx(1)): dz = Abs(bx(5) - bx(2))
            If (Abs(Abs(n(0)) - 1) < 0.001 And (Abs(dy - T) < TOL Or Abs(dz - T) < TOL)) Or _
               (Abs(Abs(n(1)) - 1) < 0.001 And (Abs(dx - T) < TOL Or Abs(dz - T) < TOL)) Then
                Print #lf, "n="; n(0); n(1); n(2); " box="; bx(0); bx(1); bx(2); bx(3); bx(4); bx(5)
            End If
        End If
    Next i
    Close #lf
End Sub
```
