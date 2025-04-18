bl_info = {
    "name": "Set Vertex Position on Axis",
    "author": "DeepSeek, Rimuru1201",
    "version": (1, 1),
    "blender": (4, 4, 1),
    "location": "View3D > Edit Mode > Vertex Context Menu",
    "description": "调整所有选中顶点的位置（支持全局/局部坐标系）",
    "category": "Mesh",
}

import bpy
import bmesh
import re
from bpy.props import StringProperty, EnumProperty

class MESH_OT_set_vertex_position(bpy.types.Operator):
    """设置选中顶点在指定轴向的位置（支持全局坐标系）"""
    bl_idname = "mesh.set_vertex_position_axis"
    bl_label = "设置顶点轴向位置"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="轴向",
        description="选择要设置的轴向",
        items=[
            ('X', "X轴", "X轴方向"),
            ('Y', "Y轴", "Y轴方向"),
            ('Z', "Z轴", "Z轴方向"),
        ],
        default='Z'
    )

    coordinate_system: EnumProperty(
        name="坐标系",
        items=[
            ('GLOBAL', "全局", "全局坐标系"),
            ('LOCAL', "局部", "局部坐标系"),
        ],
        default='GLOBAL'
    )

    position: StringProperty(
        name="位置",
        description="目标位置坐标值（支持带单位输入，如0.052m）",
        default="0.0"
    )

    def execute(self, context):
        obj = context.edit_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "无有效网格对象")
            return {'CANCELLED'}
            
        # 解析位置值
        position_str = self.position.strip()
        match = re.match(r"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?", position_str)
        if not match:
            self.report({'ERROR'}, "无效的位置值: %s" % position_str)
            return {'CANCELLED'}
        
        try:
            parsed_position = float(match.group())
        except ValueError:
            self.report({'ERROR'}, "无法解析位置值: %s" % position_str)
            return {'CANCELLED'}

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        selected_verts = [v for v in bm.verts if v.select]
        
        if not selected_verts:
            self.report({'WARNING'}, "未选中任何顶点")
            return {'CANCELLED'}

        axis_index = {'X':0, 'Y':1, 'Z':2}[self.axis]
        matrix_world = obj.matrix_world
        matrix_world_inv = matrix_world.inverted()

        for v in selected_verts:
            if self.coordinate_system == 'GLOBAL':
                # 全局坐标系处理
                global_co = matrix_world @ v.co
                global_co[axis_index] = parsed_position
                v.co = matrix_world_inv @ global_co
            else:
                # 局部坐标系处理
                v.co[axis_index] = parsed_position

        bmesh.update_edit_mesh(me)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "axis", expand=True)
        layout.prop(self, "coordinate_system")
        layout.prop(self, "position")

def menu_func(self, context):
    self.layout.operator(MESH_OT_set_vertex_position.bl_idname, 
                        text="调整选中顶点的位置")

def register():
    bpy.utils.register_class(MESH_OT_set_vertex_position)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    bpy.utils.unregister_class(MESH_OT_set_vertex_position)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()
