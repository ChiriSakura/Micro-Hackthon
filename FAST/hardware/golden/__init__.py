"""DynaX RTL 的 golden 参照模型。

每个 Verilator testbench 都需要一个能和 RTL **意见不一致**的参照。
这个包按被测单元分文件，并按依赖顺序分层：

    fixedpoint  Chisel 窄化赋值的截断行为（所有模型的基础）
    exp_unit    指数单元（PrePEA 和 RePEA 都实例化它）
    software    DynaX 自己的 Python，预测单元的判据
    execute_unit / predict_unit   各自的数据通路模型与用例

参照的选择比参照的精度更重要，三类参照对应三类问题，见各文件头。
入口是上一层的 `gen_golden.py`。
"""
