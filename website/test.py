import os
import sys
import django
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, precision_recall_fscore_support, accuracy_score
import math

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Lấy thư mục hiện tại (nơi chứa file evaluate_ai.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Thêm thư mục hiện tại vào sys.path để Python tìm thấy các app (như 'sightseeing')
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

# --- IMPORT MODULE ---
try:
    # Import chính xác theo đường dẫn file bạn cung cấp
    from sightseeing.Services.recommender import AIRecommender, Destinations
    print("✓ Đã import thành công AIRecommender từ sightseeing.Services.recommender")
except ImportError as e:
    print(f"Lỗi Import: {e}")
    print("Vui lòng đảm bảo file này nằm trong thư mục 'website' (ngang hàng với thư mục 'sightseeing')")
    sys.exit(1)

def evaluate_ai_model():
    print("="*60)
    print("BẮT ĐẦU ĐÁNH GIÁ MÔ HÌNH AI RECOMMENDER (NMF + MLP)")
    print("="*60)

    # 1. Khởi tạo mô hình
    print("\n[1] Đang khởi tạo và load dữ liệu...")
    ai = AIRecommender()
    
    if ai.user_item_matrix is None or ai.num_users == 0:
        print("Lỗi: Không có dữ liệu training trong hệ thống.")
        return

    # Lấy ma trận đánh giá
    matrix = ai.user_item_matrix
    y_true = []
    y_pred = []
    
    # Cho bài toán phân loại (Thích/Không thích)
    y_class_true = []
    y_class_pred = []
    threshold = 4.0  # Điểm >= 4.0 được coi là "Thích"

    print(f"\n[2] Đang kiểm tra độ chính xác trên {ai.num_users} users và {ai.num_items} địa điểm...")
    print("(Quá trình này có thể mất vài giây tùy lượng dữ liệu...)")
    
    count = 0
    non_zero_indices = np.transpose(np.nonzero(matrix))
    total_ratings = len(non_zero_indices)
    
    # Chỉ test trên những cặp (User, Item) đã có đánh giá thực tế
    for user_idx, item_idx in non_zero_indices:
        user_id = ai.reverse_user_map[user_idx]
        actual_rating = matrix[user_idx, item_idx]
        item_id = ai.reverse_item_map[item_idx]
        
        # Gọi hàm dự đoán của AI
        predicted_rating = ai.predict_rating(user_id, item_id)
        
        # Lưu kết quả
        y_true.append(actual_rating)
        y_pred.append(predicted_rating)
        
        # Lưu kết quả phân loại
        y_class_true.append(1 if actual_rating >= threshold else 0)
        y_class_pred.append(1 if predicted_rating >= threshold else 0)
        
        count += 1
        if count % 100 == 0 or count == total_ratings:
            print(f"    -> Đã xử lý {count}/{total_ratings} đánh giá...", end='\r')

    print(f"\n    -> Hoàn tất xử lý {total_ratings} đánh giá.")

    # --- TÍNH TOÁN VÀ HIỂN THỊ KẾT QUẢ ---
    if len(y_true) == 0:
        print("Cảnh báo: Không tìm thấy đánh giá nào để kiểm tra.")
        return

    # 1. Sai số điểm số (Regression Metrics)
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)

    print("\n" + "-"*40)
    print("KẾT QUẢ ĐÁNH GIÁ ĐỊNH LƯỢNG")
    print("-"*40)
    print(f"1. Độ chính xác dự đoán điểm (Rating Prediction):")
    print(f"   - RMSE (Sai số căn quân phương): {rmse:.4f}")
    print(f"     (Giá trị càng nhỏ càng tốt. < 1.0 là ổn)")
    print(f"   - MAE  (Sai số tuyệt đối):       {mae:.4f}")
    print(f"     (Trung bình AI lệch khoảng {mae:.2f} sao)")

    # 2. Độ chính xác gợi ý (Classification Metrics)
    precision, recall, f1, _ = precision_recall_fscore_support(y_class_true, y_class_pred, average='binary', zero_division=0)
    accuracy = accuracy_score(y_class_true, y_class_pred)

    print(f"\n2. Khả năng nhận diện sở thích (Rating >= {threshold}):")
    print(f"   - Accuracy (Độ chính xác chung): {accuracy:.2%}")
    print(f"   - Precision (Độ chính xác gợi ý): {precision:.2%}")
    print(f"     (Trong các điểm AI bảo thích, bao nhiêu % user thực sự thích?)")
    print(f"   - Recall (Độ bao phủ):            {recall:.2%}")
    print(f"     (AI tìm ra được bao nhiêu % địa điểm user thích?)")

    # --- KIỂM TRA THỰC TẾ ---
    print("\n" + "-"*40)
    print("KIỂM TRA THỰC TẾ (User mẫu)")
    print("-"*40)
    
    # Chọn User có nhiều đánh giá nhất để test
    row_sums = np.count_nonzero(matrix, axis=1)
    if np.max(row_sums) > 0:
        active_user_idx = np.argmax(row_sums)
        test_user = ai.reverse_user_map[active_user_idx]
        
        print(f"User mẫu: {test_user} (Đã tương tác với {row_sums[active_user_idx]} địa điểm)")
        
        # Top 3 địa điểm User này thích nhất (Thực tế)
        print(f"\n[THỰC TẾ] Top địa điểm {test_user} đánh giá cao:")
        user_ratings_vector = matrix[active_user_idx]
        top_indices = np.argsort(user_ratings_vector)[::-1][:3]
        
        for idx in top_indices:
            if user_ratings_vector[idx] > 0:
                item_id = ai.reverse_item_map[idx]
                try:
                    dest = Destinations.objects.get(destination_id=item_id)
                    print(f"   ★ {dest.desName} ({dest.category}): {user_ratings_vector[idx]:.1f}/5.0")
                except Destinations.DoesNotExist:
                    print(f"   ★ ID {item_id}: {user_ratings_vector[idx]:.1f}/5.0")

        # Top 5 đề xuất của AI cho User này
        print(f"\n[AI GỢI Ý] Top 5 địa điểm AI đề xuất cho {test_user}:")
        recommendations = ai.recommend_for_user(test_user, top_n=5)
        
        if not recommendations.empty:
            for _, row in recommendations.iterrows():
                print(f"   ➤ {row['name']} ({row['category']})")
                print(f"     Dự đoán: {row['predicted_rating']:.2f} | Thực tế (nếu có): {matrix[active_user_idx, ai.item_id_map[row['destination_id']]]:.1f}")
        else:
            print("   (Không có đề xuất - User có thể đã đánh giá hết các địa điểm tốt)")
    else:
        print("Không tìm thấy user nào có dữ liệu đánh giá.")

if __name__ == "__main__":
    evaluate_ai_model()
