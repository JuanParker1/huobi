# 目录
| 任务            | 目的                                          | 功能与实现                                                                                                                     | 代码路径及功能                                                                                                                                                                                                                                                                                         |
|----------------|:--------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OTC锁价订单与对冲订单的匹配| 分析对冲订单的盈亏情况，并分析盈亏是由什么因素造成的/能从什么角度改善         |                                                                                                                           | 匹配锁价订单和对冲订单，使得二者的买卖方向、币种（quote coin）、client_id 均匹配，且base_amount 的误差在 1% 以内。                                               | order_analyse文件夹下<br/>1.get_data_from_db.py：从PostgreSQL中获取锁价数据和对冲数据。<br/>2.match_order.py：订单匹配<br/>3.analyse.py：对匹配上的订单进行对冲收益等维度的分析，并可视化                                                                                                                                                        |
| 新订单异常识别与钉钉推送 | 若新订单的对冲盈亏出现异常，钉钉预警                          | 对于新进入的OTC订单，若出现以下异常情况，则推送钉钉报警：<br/>1.损益小于历史损益的 5% 分位数或大于历史损益的 95% 分位数；<br/>2.锁价报价对冲时间差大于历史对冲时间差的95%分位数。 2. OTC新订单分析并用钉钉推送 | order_analyse文件夹下：<br/>1.get_data_from_db.py：获取锁价数据和对冲数据。 <br/>2.match_order.py：订单匹配 <br/>3.push_anomalies.py：识别异常情况 <br/>4.config.json：存储参数 <br/><br/>api_and_ding文件夹下：<br/>1.ding.py：推送钉钉报警                                                                                                   |
| 锁价订单买卖匹配    | 监控客户通过买卖相同数量的同一币种从而进行套利的情况，并钉钉预警            | 对一定时间内（例如5min）输入的锁价订单进行进行同币种买卖匹配，若买卖数量相等，买卖方向相反, 就推送钉钉信息出来进行报警。                                                           | order_analyse文件夹下：<br/>1.get_data_from_db.py：获取锁价数据和对冲数据。 <br/>2.match_order_with_diff_direction.py：锁价订单买卖匹配（需要继承match_order.py中的类） <br/><br/>api_and_ding文件夹下： <br/>1.ding.py：推送钉钉报警                                                                                                           |
| OTC订单推送整合      | 整合钉钉预警的代码，便于实际执行                            | 整合新订单异常识别与钉钉推送和锁价订单买卖匹配推送的代码，每五分钟检查一次新订单情况，进行同步推送。                                                                        | order_analyse文件夹下： <br/>1.report_new_order_to_ding.py：整合新订单异常识别与钉钉推送和锁价订单买卖匹配推送的功能（实际上也需要import二者的代码）                                                                                                                                                                                           |
| 强平模拟           | 看目前的强平线设置是否合理（是否会造成损失）                      | 进行强平模拟，看在各种随机仓位和不同市场行情下，是否会触发强平线，并计算强平损失概率。                                                                               | mandatory_liquidation文件夹下：<br/>1.get_data.py：通过huobi api获取数据 <br/>2.mandatory_liquidation.py：进行模拟强平 <br/>3.paint.py：对强平结果进行可视化 <br/><br/>api_and_ding/get_market_data文件夹下： <br/>1.huobi_data.py：获取huobi交易所的行情数据                                                                                 |
| 单币种分析          | 业务需要，分析给定交易对的流动性等情况                         | 对给定的交易对，分析其在huobi、binance、okx、ftx 四个交易所的现货、永续合约交易对的行情数据，并自动生成分析报告（txt文件）。                                                 | coin_analysis文件夹下：<br/>1.exchange_data.py：整合四个交易所的api数据获取 <br/>2.coin_analysis.py：对给定交易对进行统计分析并生成报告 <br/><br/>api_and_ding/get_market_data文件夹下： <br/>1.huobi_data.py：获取huobi交易所的行情数据 <br/>2.binance_data.py：获取binance交易所的行情数据 <br/>3.okx_data.py：获取okx交易所的行情数据 <br/>4.ftx_data.py：获取ftx交易所的行情数据 |
| 子母账户功能测试（部分）  | 配资借贷业务中，看母账户对子账户的管理、限制是否能正常实现               | 测试子母账户的转账、查询等功能，由于api权限问题，部分测试未完成。                                                                                        | 见subuser_test文件夹                                                                                                                                                                                                                                                               _ |
| 价格预测       | 在质押借贷自动化对冲中，预测价格是在强平线振荡还是会持续下跌，以确定是否进行做空对冲。 | 根据波动率以及动量指标来对开盘价进行预测。 </br>未找到合适的模型进行预测，未完成。                                                                              | 见price_predict文件夹                                                                                                                                                                                                                                                                |









