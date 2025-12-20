# Báo Cáo Tiến Độ Dự Án: Sentiment Analysis on Cryptocurrency

---

## 1. Luồng Hoạt Động Hệ Thống (System Architecture Flow)

Hệ thống được thiết kế theo kiến trúc **Event-Driven Microservices**, đảm bảo khả năng xử lý dữ liệu tin tức realtime và cập nhật thông tin thị trường nhanh chóng (chu kỳ 10 phút).

### Diagram Tóm Tắt
`Crawler` → `MongoDB (Raw)` → `Kafka Producer` → `Kafka Topics` → `Consumers (AI/ML)` → `MongoDB (Enriched)` → `Airflow Aggregation` → `Backend API` → `Frontend Dashboard`

### Chi Tiết Các Bước:
1.  **Data Ingestion (Thu thập dữ liệu):**
    -   Các **Crawler** (CoinMarketCap, News Sources) chạy định kỳ 10 phút/lần (được điều phối bởi Airflow).
    -   Dữ liệu thô được lưu vào MongoDB và sinh ra [hash_id](file:///Users/khangtuan/Documents/courses/web_mining/Sentiment-Analysis-on-Social-Media-for-cryptocurrency/airflow/dags/crawler/coinmarketcap.py#57-65) duy nhất để tránh trùng lặp.
2.  **Message Queue (Kafka):**
    -   Bài viết mới được đẩy vào **Kafka Topic** để xử lý bất đồng bộ.
3.  **Processing & AI Enrichment (Xử lý thông minh):**
    -   **NLP Consumer:** Lắng nghe Kafka, thực hiện trích xuất thực thể (NER), phân tích từ khóa.
    -   **LLM Consumer (Gemini):** Đọc bài viết đã xử lý NLP, chấm điểm Sentiment (Tích cực/Tiêu cực) trên thang đo `[-1, 1]` và đánh giá độ tin cậy.
4.  **Aggregation (Tổng hợp dữ liệu):**
    -   **Airflow DAG (10-min):** Mỗi 10 phút, hệ thống gom toàn bộ bài viết trong cửa sổ thời gian, tính toán chỉ số Sentiment trung bình (Weighted Average) và lấy giá Bitcoin hiện tại (thông qua Backend/CoinPaprika).
    -   Kết quả được lưu vào collection `aggregated_features_10min`.
5.  **Serving & Visualization:**
    -   **Backend API (FastAPI):** Cung cấp API `/chart/` trả về dữ liệu lịch sử (30 ngày) kết hợp với dữ liệu realtime.
    -   **Frontend:** Hiển thị Dashboard với biểu đồ tương tác, tin tức sentiment thời gian thực.

---

## 2. Timeline & Các Công Việc Đã Hoàn Thành

### Giai Đoạn 1: Xây dựng Core Pipeline (Tuần 1-2)
- [x] Thiết lập hạ tầng Docker (Kafka, Zookeeper, MongoDB, Airflow).
- [x] Viết Crawler thu thập dữ liệu từ CoinMarketCap.
- [x] Xây dựng Kafka Producer/Consumer cơ bản.

### Giai Đoạn 2: Tích hợp AI & ML (Tuần 3-4)
- [x] Tích hợp mô hình NLP (NLTK) để phân tích text.
- [x] Kết nối Gemini LLM để chấm điểm Sentiment (Thay thế mô hình cơ bản).
- [x] Xây dựng ML API phục vụ model dự đoán giá.

### Giai Đoạn 3: Nâng cấp & Tối ưu hóa (Hiện tại)
- **Nâng cấp Realtime:** Chuyển đổi toàn bộ hệ thống từ chu kỳ 30 phút xuống **10 phút** để phản ứng nhanh hơn với thị trường.
- **Fix Data Integrity:**
    - [x] Khử trùng lặp bài viết (Deduplication) bằng [hash_id](file:///Users/khangtuan/Documents/courses/web_mining/Sentiment-Analysis-on-Social-Media-for-cryptocurrency/airflow/dags/crawler/coinmarketcap.py#57-65).
    - [x] Chuẩn hóa Timestamp (Unix epoch) toàn hệ thống.
    - [x] Fix lỗi thang đo Sentiment (từ lỗi hiển thị 1000% về chuẩn 0-100%).
- **Hoàn thiện Frontend:**
    - [x] Vẽ biểu đồ kết hợp Lịch sử (30 ngày) + Realtime.
    - [x] Xử lý lỗi Layout vỡ hiển thị.
    - [x] Tối ưu hóa UX (Time Period Switcher).

---

## 3. Các Vấn Đề Tồn Tại (Known Bugs & Limitations)

Mặc dù hệ thống đã hoạt động, vẫn còn một số vấn đề đang được monitor và xử lý:

1.  **Độ trễ khi khởi động (Cold Start):**
    -   Khi hệ thống mới khởi động lại, Frontend có thể mất 1-2 phút hiển thị "Fetching..." do các container Crawler/Consumer đang khởi tạo connection.
2.  **Phụ thuộc API bên thứ 3:**
    -   Việc lấy giá Bitcoin phụ thuộc vào CoinPaprika/CoinGecko. Nếu các API này bị Rate Limit, biểu đồ giá có thể bị khuyết một số điểm dữ liệu realtime (Hệ thống đã có cơ chế fallback nhưng chưa hoàn hảo 100%).
3.  **UI Refinement:**
    -   Trên một số màn hình độ phân giải siêu rộng (Ultrawide), bố cục Dashboard có thể bị giãn nhẹ (đang tinh chỉnh CSS).
4.  **Dữ liệu rác lịch sử:**
    -   Một số bản ghi cũ trong DB (trước khi fix lỗi thang đo) có thể vẫn còn giá trị sentiment sai lệch (nhóm đã viết script fix nhưng cần chạy rà soát định kỳ).

---

**Kết luận:** Hệ thống đã hoàn thiện về mặt chức năng và sẵn sàng demo. Các vấn đề còn lại chủ yếu là tối ưu hóa vận hành và trải nghiệm người dùng (UX).
