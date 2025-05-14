import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

basepairs = ('A', 'G', 'C', 'T')
color = {'A':(1,0,0), 'G':(0,1,0), 'C':(0,0,1), 'T':(.5,.5,.5)}
# Torus, Spiral and Codon Data
mj_radius = 10
mn_radius = 8

spiral_loops = 10       # Number of spiral loops around the torus
points_per_loop = 100   # Resolution of the spiral
spiral_thickness = 0.08 # Thickness of spiral strand
bp_thickness = 0.04     # Thickness of basepair strands

# Create the spiral path as a curve
curve_data = bpy.data.curves.new(name='SpiralCurve', type='CURVE')
curve_data.dimensions = '3D'
spline1 = curve_data.splines.new(type='POLY')
spline1.points.add(spiral_loops * points_per_loop - 1)
spline2 = curve_data.splines.new(type='POLY')
spline2.points.add(spiral_loops * points_per_loop - 1)


for i in range(spiral_loops * points_per_loop):

    t = 2*math.pi*i/(spiral_loops*points_per_loop)
    w = spiral_loops
    # Parametric equations for torus with spiral
    R = (mj_radius + mn_radius)//2
    r = (mj_radius - mn_radius)//2
    z1 = (R + r*math.sin(w*t)) * math.cos(t)
    y1 = (R + r*math.sin(w*t)) * math.sin(t)
    x1 = r*math.cos(w*t)
    z2 = (R - r*math.sin(w*t)) * math.cos(t)
    y2 = (R - r*math.sin(w*t)) * math.sin(t)
    x2 = -r*math.cos(w*t)
    spline1.points[i].co = (x1, y1, z1, 1)
    spline2.points[i].co = (x2, y2, z2, 1)
    
    if i % 10 == 0:
        # Midpoint
        mx, my, mz = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2

        # Generate basepair
        bp1 = random.choice(basepairs)
        bp2 = basepairs[len(basepairs) - basepairs.index(bp1) - 1]  # simple complement

        # Create first strand basepair curve
        strand1_basepair_data = bpy.data.curves.new(name=f'Strand1_lineCurve{i}', type='CURVE')
        strand1_basepair_data.dimensions = '3D'
        spline1_bp = strand1_basepair_data.splines.new(type='POLY')
        spline1_bp.points.add(1)
        spline1_bp.points[0].co = (x1, y1, z1, 1)
        spline1_bp.points[1].co = (mx, my, mz, 1)
        obj1 = bpy.data.objects.new(f"Strand1_Line{i}", strand1_basepair_data)
        bpy.context.collection.objects.link(obj1)
        strand1_basepair_data.bevel_depth = bp_thickness

        mat1 = bpy.data.materials.new(name=f"Mat_{bp1}_{i}")
        mat1.use_nodes = True
        bsdf1 = mat1.node_tree.nodes.get("Principled BSDF")
        bsdf1.inputs["Base Color"].default_value = (*color[bp1], 1)
        bsdf1.inputs["Metallic"].default_value = 0.9 
        bsdf1.inputs["Roughness"].default_value = 0.3
        obj1.data.materials.append(mat1)

        # Create second strand basepair curve
        strand2_basepair_data = bpy.data.curves.new(name=f'Strand2_lineCurve{i}', type='CURVE')
        strand2_basepair_data.dimensions = '3D'
        spline2_bp = strand2_basepair_data.splines.new(type='POLY')
        spline2_bp.points.add(1)
        spline2_bp.points[0].co = (mx, my, mz, 1)
        spline2_bp.points[1].co = (x2, y2, z2, 1)
        obj2 = bpy.data.objects.new(f"Strand2_Line{i}", strand2_basepair_data)
        bpy.context.collection.objects.link(obj2)
        strand2_basepair_data.bevel_depth = bp_thickness

        mat2 = bpy.data.materials.new(name=f"Mat_{bp2}_{i}")
        mat2.use_nodes = True
        bsdf2 = mat2.node_tree.nodes.get("Principled BSDF")
        bsdf2.inputs["Base Color"].default_value = (*color[bp2], 1)
        bsdf2.inputs["Metallic"].default_value = 0.9 
        bsdf2.inputs["Roughness"].default_value = 0.3
        obj2.data.materials.append(mat2)

# Create the object from the curve
curve_obj = bpy.data.objects.new('SpiralStrand', curve_data)
bpy.context.collection.objects.link(curve_obj)

curve_data.bevel_depth = spiral_thickness
curve_data.bevel_resolution = 4

# Give material to strand
mat = bpy.data.materials.new(name="StrandMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (1, 0.6, 0.2, 1)
bsdf.inputs["Metallic"].default_value = 0.8
bsdf.inputs["Roughness"].default_value = 0.4

# Assign material
curve_obj.data.materials.append(mat)

# Step 1: Collect curve objects and their spline materials
curve_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'CURVE']
spline_materials = []

for obj in curve_objects:
    for spline in obj.data.splines:
        mat = obj.data.materials[0] if obj.data.materials else None
        spline_materials.append((spline, mat))  # Pair spline and its mat and store in a list

# Step 2: Deselect all, select only curves
bpy.ops.object.select_all(action='DESELECT')
# Alternative approach to deselect:
#for obj in bpy.data.objects:
#    obj.select_set(False)
for obj in curve_objects:
    obj.select_set(True)

# Step 3: Make one of them active (needed for joining)
bpy.context.view_layer.objects.active = curve_objects[0]

# Step 4: Join the curves
bpy.ops.object.join()
joined_obj = bpy.context.active_object

# Step 5: Clean up materials and reassign
joined_curve = joined_obj.data
joined_obj.data.materials.clear()

# Make a list of unique materials and assign slots
unique_mats = list({mat for _, mat in spline_materials if mat is not None})
for mat in unique_mats:
    joined_obj.data.materials.append(mat)

# Assign material index to each spline based on original mapping
for i, spline in enumerate(joined_curve.splines):
    orig_mat = spline_materials[i][1]
    if orig_mat:
        mat_index = unique_mats.index(orig_mat)
        spline.material_index = mat_index

