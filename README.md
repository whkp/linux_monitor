# Linux系统监控项目

## 项目概述

这是一个基于C++和gRPC的Linux系统监控解决方案，能够实时监控Linux系统的各种性能指标，包括CPU使用率、内存使用情况、网络状态等。项目采用客户端-服务器架构，通过Qt界面进行可视化展示。

## 项目特性

- 🖥️ **实时系统监控**: 监控CPU、内存、网络、中断等系统指标
- 🌐 **分布式架构**: 基于gRPC的客户端-服务器通信
- 🎨 **可视化界面**: 使用Qt框架开发的现代化GUI
- 📊 **多指标监控**: 支持CPU负载、软中断、内存统计、网络流量等
- 🔧 **模块化设计**: 清晰的模块划分，易于扩展和维护

## 项目架构

### 整体架构图

```
┌─────────────────┐    gRPC     ┌─────────────────┐    数据收集    ┌─────────────────┐
│   Qt GUI界面    │  ◄────────► │   gRPC服务器    │  ◄────────────► │   监控模块群    │
│ (display_monitor)│             │ (rpc_manager)   │                │ (test_monitor)  │
└─────────────────┘             └─────────────────┘                └─────────────────┘
        │                               │                                    │
        │                               │                                    │
        ▼                               ▼                                    ▼
┌─────────────────┐             ┌─────────────────┐                ┌─────────────────┐
│   UI组件模型    │             │   Protocol      │                │   /proc文件系统 │
│   (Models)      │             │   Buffers       │                │   系统数据源    │
└─────────────────┘             └─────────────────┘                └─────────────────┘
```

### 模块详细说明

#### 1. Proto模块 (`proto/`)
- **功能**: 定义gRPC服务接口和数据结构
- **主要文件**:
  - `monitor_info.proto`: 主服务接口定义
  - `cpu_load.proto`: CPU负载数据结构
  - `cpu_stat.proto`: CPU统计数据结构
  - `cpu_softirq.proto`: 软中断数据结构
  - `mem_info.proto`: 内存信息数据结构
  - `net_info.proto`: 网络信息数据结构

#### 2. 数据收集模块 (`test_monitor/`)
- **功能**: 负责从Linux系统收集各种监控数据
- **核心组件**:
  - `CpuStatMonitor`: 从`/proc/stat`收集CPU使用统计
  - `CpuLoadMonitor`: 从`/proc/loadavg`收集系统负载
  - `CpuSoftIrqMonitor`: 从`/proc/softirqs`收集软中断信息
  - `MemMonitor`: 从`/proc/meminfo`收集内存使用信息
  - `NetMonitor`: 从`/proc/net/dev`收集网络流量统计

#### 3. RPC管理模块 (`rpc_manager/`)
- **功能**: 提供gRPC服务，处理客户端请求
- **组件**:
  - `server/`: gRPC服务器实现
  - `client/`: gRPC客户端库
  - `GrpcManagerImpl`: 服务接口实现类

#### 4. 显示模块 (`display_monitor/`)
- **功能**: Qt GUI界面，实时显示监控数据
- **核心组件**:
  - `MonitorWidget`: 主监控界面
  - `CpuLoadModel`: CPU负载显示模型
  - `CpuStatModel`: CPU统计显示模型
  - `MemModel`: 内存监控显示模型
  - `NetModel`: 网络监控显示模型

## Linux系统监控实现原理

### 1. CPU监控实现

#### CPU使用率统计 (`/proc/stat`)
```cpp
// 从/proc/stat读取CPU时间片信息
user nice system idle iowait irq softirq steal guest guest_nice
```

**实现原理**:
- 读取每个CPU核心的时间片数据
- 计算两次采样间隔内的时间差
- 使用公式: `CPU使用率 = (total_time - idle_time) / total_time * 100%`

#### CPU负载监控 (`/proc/loadavg`)
```cpp
// 读取系统平均负载
load_avg_1min load_avg_5min load_avg_15min running_processes/total_processes last_pid
```

#### 软中断监控 (`/proc/softirqs`)
- 监控不同类型的软中断：HI、TIMER、NET_TX、NET_RX、BLOCK等
- 计算各CPU核心上不同类型软中断的频率

### 2. 内存监控实现

#### 内存信息收集 (`/proc/meminfo`)
```cpp
// 关键内存指标
MemTotal:    总内存大小
MemFree:     空闲内存
MemAvailable: 可用内存
Buffers:     缓冲区内存
Cached:      页面缓存
SwapTotal:   交换分区总大小
SwapFree:    交换分区空闲大小
```

**实现算法**:
- 内存使用率 = `(MemTotal - MemAvailable) / MemTotal * 100%`
- 缓存使用情况 = `(Buffers + Cached) / MemTotal * 100%`

### 3. 网络监控实现

#### 网络接口统计 (`/proc/net/dev`)
```cpp
// 网络接口数据格式
interface: bytes packets errs drop fifo frame compressed multicast
```

**实现方法**:
- 定期采样网络接口的字节数和包数
- 计算时间间隔内的传输速率
- 支持多网络接口监控

### 4. 数据流处理

```
┌─────────────┐    读取     ┌─────────────┐    解析     ┌─────────────┐
│ /proc文件   │ ────────► │   原始数据   │ ────────► │   结构化数据 │
└─────────────┘           └─────────────┘           └─────────────┘
                                 │
                                 ▼
┌─────────────┐    推送     ┌─────────────┐    计算     ┌─────────────┐
│ gRPC客户端  │ ◄────────── │   监控数据   │ ◄────────── │   数据处理   │
└─────────────┘           └─────────────┘           └─────────────┘
```

## 编译和运行

### 依赖项要求

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    cmake \
    build-essential \
    pkg-config \
    libgrpc++-dev \
    libprotobuf-dev \
    protobuf-compiler-grpc \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools

# CentOS/RHEL
sudo yum install -y \
    cmake3 \
    gcc-c++ \
    grpc-devel \
    protobuf-devel \
    qt5-qtbase-devel
```

### 编译步骤

```bash
# 克隆项目
git clone <repository-url>
cd linux_monitor

# 创建构建目录
mkdir build && cd build

# 配置CMake
cmake ..

# 编译项目
make -j$(nproc)
```

### 运行系统

#### 1. 启动gRPC服务器
```bash
# 在终端1中运行
cd build/rpc_manager/server
./server
```

#### 2. 启动数据收集客户端
```bash
# 在终端2中运行
cd build/test_monitor/src
./monitor_test
```

#### 3. 启动GUI显示界面
```bash
# 在终端3中运行
cd build/display_monitor
./display [server_address]  # 默认: localhost:50051
```

## 配置说明

### gRPC服务配置
- 默认服务端口: `50051`
- 数据更新频率: `3秒` (数据收集端)
- GUI刷新频率: `2秒` (显示端)

### 监控数据源
- CPU统计: `/proc/stat`
- 系统负载: `/proc/loadavg`
- 软中断: `/proc/softirqs`
- 内存信息: `/proc/meminfo`
- 网络统计: `/proc/net/dev`

## 项目扩展

### 添加新的监控指标

1. **定义Proto消息**:
```protobuf
// 在proto/目录下创建新的.proto文件
message NewMonitorData {
    string name = 1;
    float value = 2;
}
```

2. **实现监控类**:
```cpp
// 在test_monitor/src/monitor/目录下
class NewMonitor : public MonitorInter {
public:
    void UpdateOnce(monitor::proto::MonitorInfo* monitor_info) override;
};
```

3. **添加显示模型**:
```cpp
// 在display_monitor/目录下
class NewModel : public QAbstractTableModel {
    // Qt模型实现
};
```

### 性能优化建议

1. **数据采样优化**:
   - 根据需求调整采样频率
   - 实现数据缓存机制
   - 使用异步I/O读取proc文件

2. **网络优化**:
   - 启用gRPC压缩
   - 实现数据增量传输
   - 添加连接池管理

3. **界面优化**:
   - 实现数据绑定
   - 添加图表可视化
   - 支持主题切换

## 故障排除

### 常见问题

1. **编译错误**:
   - 检查依赖项是否完整安装
   - 确认CMake版本 >= 3.10
   - 验证protobuf和gRPC版本兼容性

2. **运行时错误**:
   - 确认gRPC服务器正常启动
   - 检查防火墙端口设置
   - 验证/proc文件系统访问权限

3. **数据异常**:
   - 检查系统负载情况
   - 确认监控间隔设置合理
   - 验证数据解析逻辑

## 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [维护者姓名]
- 邮箱: [联系邮箱]
- 项目地址: [GitHub链接]
