# pairwise-taa

实时游戏画面一开 TAA，快速转身时角色轮廓就出鬼影：history 采样没有按 velocity 重投影；depth 变化大的像素没有做 disocclusion 标记，遮挡边缘拖出长条；jitter 序列在奇数分辨率下不居中，画面整体偏移半个像素；HDR 颜色在 history 里被 clamp 到 LDR，霓虹灯变灰；相机 cut 后 history 没清，切镜头第一帧全是残影；运动矢量在蒙皮角色上只用了骨骼矩阵，布料和粒子没有 velocity。render/taa.py 是核心，tests/test_taa.py 15个红。要修的是：按 velocity 重投影并做 neighborhood clamp；用 depth/normal 做 disocclusion；jitter 按分辨率居中；history 保持 HDR；相机 cut 清 history；为蒙皮/布料/粒子补运动矢量。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。

语言/框架：Python 3, pytest；环境可复现等级：无外部依赖。
