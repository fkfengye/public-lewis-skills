# DF-01 原图分析与特征清单

原图经用户授权保存与展示；其中登录、注册、凭证及短信业务仅是来源事实，不作为通用数据流的默认内容。没有给出符号图例，因此只描述实际所见，不认定为某一正式 DFD 标准。

## 画布、布局与图元

- 原 PNG 1635×1075，RGB 不透明白底，宽高比约 1.52。无标题、图例、分区边界或装饰图案；顶部与左右留白，主体靠中下方，以节点与线条形成疏朗的非对称网络。
- 六个节点：左下粉色矩形 User；中下浅蓝圆形 Web/App Client；中上浅蓝圆形 Registration Service；右下浅蓝圆形 Authentication Service；顶部浅绿矩形 SMS/OTP Service；右上浅黄矩形 User database。它们分别表现外部用户、三个处理过程、外部服务与数据存储；不根据矩形形状混淆实体和存储，不凭外观推断部署或信任边界。
- 大圆内文字分多行居中；矩形尺寸略不同、近直角。组件为深色细实线轮廓，右下露出同色系更深的薄条，形成硬边、无模糊的偏移色影：蓝色圆影、粉、绿、黄矩形影。数据库是黄色矩形而非圆柱，这不证明该符号是通用标准；节点无图标。
- 英文节点文本具手写感；线边标签更规整、近似等宽字体。文字近黑；节点居中，长的线边标签换两行。截图无法确定实际字体，可用手写字族与可读的中文后备字体近似。

## 连线、数据与不确定项

细黑直线和实心黑三角箭头；主要水平或垂直，无虚线、曲线、折点、图例或序号。不同方向的数据流分为独立平行线、分离端口、各自箭头；线边标签处留有白色断口。新图应预先划分真实间距，不用白色遮罩掩盖线穿字。

| 原图数据流 | 数据标注 | 方向 |
| --- | --- | --- |
| User → Web/App Client | email, phone, password / OTP | 向右 |
| Web/App Client → User | session/bearer token | 向左 |
| Web/App Client → Registration Service | user data | 向上 |
| Registration Service → SMS/OTP Service | send OTP (phone) | 向上 |
| SMS/OTP Service → Registration Service | OTP id / status | 向下 |
| Registration Service → User database | create/verify user, audit logs | 向右 |
| Web/App Client → Authentication Service | login requests | 向右 |
| Authentication Service → Web/App Client | JWT access & refresh | 向左 |
| User database — Authentication Service | read user, write login logs | 仅见标注连线，未见明确箭头；方向、是否为一条或多条流待确认 |

数据内容按原图记录，不自动表示请求、响应、协议、同步或执行顺序；最后一条不能依据文字自行添加箭头或拆分方向。原图未明确声明步骤编号、边界、存储实现及控制顺序。

## 颜色和样例覆盖

近似色：白底 #FFFFFF；圆填充 #C0E4FF、圆影 #4DABF7；用户粉底 #FDD4E3、粉影 #F783AC；服务绿底 #B2F2BB、绿影近 #69DB7C；存储黄底 #FFEC99、黄影 #FFD43B；线与字 #1E1E1E。抗锯齿会引入周围色值，RGB 白底不是透明像素。

| 原图特征 | 通用示例 |
| --- | --- |
| 无标题白底、留白及非对称布局 | 保留 |
| 三个大圆、粉绿黄矩形及对应硬边错位色影 | 保留并新增一个外部对象 |
| 深色细线、实心三角、分离的双向线、标签及真实断口 | 保留 |
| 数据存储非圆柱图元、手写感文字与规整边标签 | 保留；字体使用可用后备近似 |
| 方向不明的标注线 | 用无箭头线展示并明确写方向待确认 |

示例使用独立构造的虚构内容发布业务，新增外部对象和数据边，业务、节点和拓扑并非原图复刻。用户原图通过目录单独查看。
