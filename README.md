# Aicup
python環境配置：
pip install num2words numpy torch pandas

google colab環境配置：見models中相關程式Environment部分

數據處理流程說明：
1.使用data_processing/data_processing_task1_1127.py 分別生成任務1所需的train/test/val data。結果如data文件夾中所示。
2.使用data_processing/data_processing_task2.py 分別生成任務2所需的train/test data。結果如data文件夾中所示。
3.使用models中的相關模型，通過完成google colab中task1相關的模型訓練，並得到對val data的預測文件prediction_xxxxxxxx.
4.通過data_processing/annotation.py文件對得的prediction_xxxxxxxx預測結果進行標註
