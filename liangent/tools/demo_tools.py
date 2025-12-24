from liangent.tools.registry import tool

@tool
def calculate_bmi(weight: float, height: float) -> float:
    """
    计算 Body Mass Index (BMI)。

    Args:
        weight: 体重（公斤）。
        height: 身高（米）。
    """
    return weight / (height * height)
