# 📈 Cryptocurrency Sentiment Analysis & Price Prediction

Hệ thống phân tích cảm xúc thị trường tiền điện tử (Bitcoin) từ tin tức và dự đoán biến động giá sử dụng Machine Learning.

## 🌟 Giới Thiệu

Dự án này xây dựng một pipeline dữ liệu hoàn chỉnh (End-to-End Data Pipeline) để:
1.  **Thu thập dữ liệu (Crawling):** Tự động cào tin tức mới nhất về Bitcoin từ CoinMarketCap.
2.  **Phân tích cảm xúc (Sentiment Analysis):** Sử dụng LLM (Google Gemini) để đọc hiểu và phân loại tin tức thành các nhóm cảm xúc cụ thể (Reporting, Manipulation, Positive, Negative).
3.  **Gán nhãn dữ liệu (Data Labeling):** Kết hợp cảm xúc với biến động giá Bitcoin thực tế sau 1 giờ để tạo bộ dữ liệu huấn luyện.
4.  **Huấn luyện mô hình (ML Training):** Tự động huấn luyện các mô hình Machine Learning để dự đoán giá Bitcoin dựa trên cảm xúc tin tức.
5.  **Trực quan hóa (Dashboard):** Hiển thị tin tức, chỉ số cảm xúc và dự đoán giá lên giao diện web.

## 🚀 Tính Năng Chính

### 1. Thu Thập Tin Tức Tự Động (Data Ingestion)
*   **Nguồn:** CoinMarketCap News.
*   **Công nghệ:** Airflow DAG (`cmc_news_24h`) chạy định kỳ mỗi giờ.
*   **Cơ chế:** Crawler lấy tin -> Đẩy vào Kafka Topic (`coinmarketcap-news`) -> Lưu vào MongoDB (`cmc_news`).

### 2. Phân Tích Cảm Xúc Thông Minh (AI Sentiment Analysis)
*   **Công nghệ:** Google Gemini 1.5 Flash (LLM).
*   **Cơ chế:** Kafka Consumer đọc tin từ Kafka -> Gửi nội dung cho LLM phân tích.
*   **Phân loại cảm xúc (4 loại):**
    *   🔵 **Bitcoin Reporting:** Tin tức đưa tin khách quan, thực tế.
    *   🟣 **Bitcoin Price Manipulation:** Tin đồn thổi, thao túng giá không có căn cứ.
    *   🟢 **Bitcoin Positive Speculation:** Dự đoán tích cực có cơ sở.
    *   🔴 **Bitcoin Negative Speculation:** Dự đoán tiêu cực có cơ sở.
*   **Lưu trữ:** Cập nhật kết quả phân tích (Label, Score, Reasoning) ngược lại vào bản ghi tin tức gốc trong MongoDB.

### 3. Tự Động Gán Nhãn Dữ Liệu (Auto Labeling)
*   **Mục đích:** Tạo dữ liệu Training cho mô hình ML (Supervised Learning).
*   **Công nghệ:** Airflow DAG (`label_data`) chạy mỗi 2 giờ.
*   **Logic:**
    *   Tìm các bài báo đã phân tích cảm xúc và cũ hơn 1 giờ.
    *   Lấy giá Bitcoin tại thời điểm bài báo ra đời (T) và sau đó 1 giờ (T+1h).
    *   Tính toán biến động giá (Tăng/Giảm) làm nhãn (Target).
    *   Lưu vào collection `cmc_labeled_data`.

### 4. Pipeline Huấn Luyện & Triển Khai ML (MLOps)
*   **Công nghệ:** Airflow, MLflow, Scikit-learn.
*   **Quy trình (DAG `price_prediction_pipeline`):**
    *   **Extract:** Lấy dữ liệu đã gán nhãn từ MongoDB.
    *   **Train:** Huấn luyện 3 mô hình (Linear Regression, Random Forest, Gradient Boosting).
    *   **Evaluate:** So sánh hiệu quả (MAE, MSE) và chọn mô hình tốt nhất.
    *   **Register:** Đăng ký mô hình tốt nhất vào MLflow Model Registry (Production).
    *   **Deploy:** Backend API tự động tải mô hình mới nhất để phục vụ dự đoán.

### 5. Dashboard Theo Dõi (Frontend)
*   **Giao diện:** Hiển thị tin tức realtime.
*   **Sentiment:** Hiển thị nhãn cảm xúc và lý do (Reasoning) của AI cho từng bài báo.
*   **Prediction:** Hiển thị dự đoán xu hướng giá Bitcoin.

## 🏗 Kiến Trúc Hệ Thống

```mermaid
graph TD
    subgraph Data Collection
        CMC[CoinMarketCap] -->|Crawl| Airflow[Airflow Crawler DAG]
        Airflow -->|Push| Kafka[Kafka Topic]
        Airflow -->|Save Raw| Mongo[MongoDB (cmc_news)]
    end

    subgraph Processing & AI
        Kafka -->|Consume| Consumer[Backend Consumer]
        Consumer -->|Analyze| Gemini[Gemini LLM]
        Gemini -->|Result| Consumer
        Consumer -->|Update Sentiment| Mongo
        Consumer -->|Save Unlabeled| MongoUnlabeled[MongoDB (cmc_unlabeled_data)]
    end

    subgraph Data Labeling
        MongoUnlabeled -->|Read| LabelDAG[Airflow Label DAG]
        CoinAPI[CoinRanking API] -->|Get Price| LabelDAG
        LabelDAG -->|Save Labeled| MongoLabeled[MongoDB (cmc_labeled_data)]
    end

    subgraph Machine Learning
        MongoLabeled -->|Train Data| TrainDAG[Airflow Training DAG]
        TrainDAG -->|Log Exp| MLflow[MLflow Tracking]
        TrainDAG -->|Register Model| ModelReg[MLflow Registry]
    end

    subgraph Serving
        ModelReg -->|Load Model| API[Backend ML API]
        Mongo -->|Get News| API
        API -->|Serve JSON| Frontend[Web Dashboard]
    end
```

## 🛠 Cài Đặt & Chạy Dự Án

### Yêu Cầu
*   Docker & Docker Compose
*   Make (Optional)

### Các Bước
1.  **Clone Repository:**
    ```bash
    git clone <repo_url>
    cd Sentiment-Analysis-on-Social-Media-for-cryptocurrency
    ```

2.  **Cấu Hình Môi Trường:**
    *   Tạo file `.env` từ `.env.example`.
    *   Điền API Key (Gemini, CoinRanking, vv).

3.  **Khởi Động Hệ Thống:**
    ```bash
    make up
    # Hoặc: docker-compose up -d --build
    ```

4.  **Truy Cập:**
    *   **Frontend:** http://localhost:3000
    *   **Airflow UI:** http://localhost:8080 (user/pass: airflow/airflow)
    *   **MLflow UI:** http://localhost:5001
    *   **API Docs:** http://localhost:8000/docs

## 📂 Cấu Trúc Thư Mục

*   `airflow/`: Chứa các DAGs (Crawler, Labeling, Training).
*   `backend/`: Source code Backend (FastAPI, Consumer, LLM Agent).
*   `frontend/`: Source code Frontend (HTML/CSS/JS).
*   `docker-compose.yaml`: Cấu hình Docker services.

## 📝 Ghi Chú
*   Hệ thống cần khoảng 1-2 giờ để tích lũy đủ dữ liệu cho quy trình Labeling và Training hoạt động lần đầu tiên.
*   Đảm bảo Kafka và Zookeeper khởi động thành công (check logs nếu gặp lỗi connection).
