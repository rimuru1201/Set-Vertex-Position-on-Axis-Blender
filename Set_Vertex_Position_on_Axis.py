bl_info = {
    "name": "Set Vertex Position on Axis",
    "author": "DeepSeek, Rimuru1201",
    "version": (1, 2),
    "blender": (4, 4, 1),
    "location": "View3D > Edit Mode > Vertex Context Menu",
    "description": "调整所有选中顶点的位置（支持全局/局部坐标系和四则运算）",
    "category": "Mesh",
}

import bpy
import bmesh
import re
from mathutils import Vector
from bpy.props import StringProperty, EnumProperty

class MESH_OT_set_vertex_position(bpy.types.Operator):
    """支持数学表达式的顶点位置设置"""
    bl_idname = "mesh.set_vertex_position_axis"
    bl_label = "设置顶点轴向位置"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="轴向",
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
        description="支持四则运算（示例：0.1+0.05*2）",
        default="0.0"
    )

    def safe_eval(self, expr):
        """安全计算数学表达式"""
        # 清理表达式（允许数字、运算符和小数点）
        clean_expr = re.sub(r"[^\d\.\+\-\*/\(\) ]", "", expr)
        try:
            return eval(clean_expr, {"__builtins__": None}, {})
        except Exception as e:
            self.report({'ERROR'}, f"计算错误: {str(e)}")
            return None

    def execute(self, context):
        obj = context.edit_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "无有效网格对象")
            return {'CANCELLED'}
            
        # 解析并计算表达式
        parsed_value = self.safe_eval(self.position)
        if parsed_value is None:
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
                global_co = matrix_world @ v.co
                global_co[axis_index] = parsed_value
                v.co = matrix_world_inv @ global_co
            else:
                v.co[axis_index] = parsed_value

        bmesh.update_edit_mesh(me)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "axis", expand=True)
        layout.prop(self, "coordinate_system")
        layout.prop(self, "position")
        layout.label(text="支持加减乘除（示例：0.1+0.05*2）", icon='INFO')

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
