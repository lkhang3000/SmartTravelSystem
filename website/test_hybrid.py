import os
import sys
import time
import django
import pandas as pd
import numpy as np
from collections import Counter

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

# Import các thuật toán từ file recommender.py
try:
    from sightseeing.Services.recommender import ContentSimilarityRecommender, UserBehaviorRecommender, HybridRecommender
    from sightseeing.models import Destinations, UserRating
    print("✓ Đã import thành công các thuật toán.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def evaluate_algorithms():
    print("\n" + "="*60)
    print("ĐÁNH GIÁ CÁC THUẬT TOÁN CỔ ĐIỂN (NON-AI)")
    print("="*60)

    # ---------------------------------------------------------
    # 1. ĐÁNH GIÁ CONTENT-BASED FILTERING (Dựa trên nội dung)
    # ---------------------------------------------------------
    print("\n[1] Đánh giá Content-Based Filtering (TF-IDF & Metadata)")
    cb = ContentSimilarityRecommender()
    
    # Test case: Người dùng thích 'Beach' (Biển)
    test_pref = {'category': 'Beach'}
    print(f"   Input: Sở thích = {test_pref['category']}")
    
    start_time = time.time()
    cb_results = cb.recommend_by_preferences(test_pref, top_n=10)
    duration = (time.time() - start_time) * 1000 # ms

    if not cb_results.empty:
        # Tính độ chính xác: Bao nhiêu % kết quả đúng là category 'Beach'
        correct_category = cb_results[cb_results['category'] == 'Beach']
        accuracy = (len(correct_category) / len(cb_results)) * 100
        
        print(f"   Thời gian xử lý: {duration:.2f} ms")
        print(f"   Độ chính xác (Category Match): {accuracy:.1f}%")
        print("   Top 3 kết quả:")
        for _, row in cb_results.head(3).iterrows():
            print(f"     - {row['name']} ({row['category']}) | Score: {row['preference_score']:.2f}")
    else:
        print("   Không có kết quả (Cần kiểm tra lại dữ liệu Destinations).")

    # ---------------------------------------------------------
    # 2. ĐÁNH GIÁ COLLABORATIVE FILTERING (Memory-Based)
    # ---------------------------------------------------------
    print("\n[2] Đánh giá User Behavior Collaborative (Item-Item Similarity)")
    ub = UserBehaviorRecommender()
    
    if ub.user_item_matrix is not None and not ub.user_item_matrix.empty:
        # Tìm user hoạt động tích cực nhất để test
        user_counts = ub.user_item_matrix.astype(bool).sum(axis=1)
        active_user = user_counts.idxmax()
        
        print(f"   User Test: {active_user} (Đã tương tác {user_counts[active_user]} địa điểm)")
        
        start_time = time.time()
        ub_results = ub.recommend_for_user(active_user, top_n=10)
        duration = (time.time() - start_time) * 1000

        if not ub_results.empty:
            print(f"   Thời gian xử lý: {duration:.2f} ms")
            
            # Đánh giá độ đa dạng (Diversity)
            unique_cats = ub_results['category'].nunique()
            diversity_score = (unique_cats / len(ub_results)) * 100
            
            print(f"   Độ đa dạng danh mục (Diversity): {diversity_score:.1f}%")
            print("   Top 3 kết quả:")
            for _, row in ub_results.head(3).iterrows():
                print(f"     - {row['name']} ({row['category']}) | Sim-Score: {row['similarity_score']:.2f}")
        else:
            print("   Không đủ dữ liệu để gợi ý cho user này.")
    else:
        print("   ⚠️ Không có dữ liệu đánh giá (User-Item Matrix rỗng).")

    # ---------------------------------------------------------
    # 3. SO SÁNH HIỆU SUẤT (BENCHMARK)
    # ---------------------------------------------------------
    print("\n[3] So sánh Hiệu suất & Logic (Hybrid Benchmark)")
    hybrid = HybridRecommender()
    
    # Lấy 1 địa điểm bất kỳ để tìm điểm tương đồng
    if Destinations.objects.exists():
        sample_dest = Destinations.objects.first()
        dest_id = sample_dest.destination_id
        print(f"   Test tìm địa điểm tương đồng với: {sample_dest.desName}")

        # Đo Content-Based
        t1 = time.time()
        res_cb = hybrid.content_based.get_similar_by_content(dest_id, top_n=5)
        t_cb = (time.time() - t1) * 1000

        # Đo Collaborative
        t2 = time.time()
        res_collab = hybrid.collaborative.get_similar_destinations(dest_id, user_rating=5.0, top_n=5)
        t_collab = (time.time() - t2) * 1000

        print(f"\n   {'ALGORITHM':<20} | {'TIME (ms)':<10} | {'TOP 1 RESULT'}")
        print("-" * 60)
        
        top_cb = res_cb.iloc[0]['name'] if not res_cb.empty else "N/A"
        print(f"   {'Content-Based':<20} | {t_cb:<10.2f} | {top_cb}")
        
        top_col = res_collab.iloc[0]['name'] if not res_collab.empty else "N/A"
        print(f"   {'Collaborative':<20} | {t_cb:<10.2f} | {top_col}")

        # Kết luận ngắn
        print("\n   ---> NHẬN XÉT:")
        if t_cb < t_collab:
            print("   • Content-Based nhanh hơn (Phù hợp khi User mới chưa có lịch sử).")
        else:
            print("   • Collaborative nhanh hơn (Phù hợp khi hệ thống đã có nhiều dữ liệu rating).")
            
        if top_cb != top_col:
            print("   • Hai thuật toán đưa ra kết quả KHÁC NHAU -> Hybrid là cần thiết để bù trừ.")
        else:
            print("   • Hai thuật toán đồng thuận -> Độ tin cậy cao.")

    else:
        print("   Không có dữ liệu Destination để test.")

if __name__ == "__main__":
    evaluate_algorithms()
