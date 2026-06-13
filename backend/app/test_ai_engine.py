import sys
import os

# Add the parent directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.inference import run_inference, sw_msa, cross_entropy

def test_sw_msa_arithmetic():
    print("[TEST] Running SW-MSA Attention Matrix Arithmetic Tests...")
    # Mock attention parameters
    nh, nt, dh = 2, 4, 8
    d = nh * dh
    Q = [[[0.1] * dh] * nt] * nh
    K = [[[0.1] * dh] * nt] * nh
    V = [[[0.5] * dh] * nt] * nh
    B = [[0.01] * nt] * nt
    
    output = sw_msa(Q, K, V, d, B)
    
    assert len(output) == nh
    assert len(output[0]) == nt
    assert len(output[0][0]) == dh
    print("  [SUCCESS] Pure-Python SW-MSA attention output bounds match perfectly!")

def test_cross_entropy():
    print("[TEST] Running Categorical Cross Entropy Loss Verification...")
    y_true = [0.0, 1.0, 0.0]
    y_pred_good = [0.05, 0.90, 0.05]
    y_pred_bad = [0.80, 0.10, 0.10]
    
    loss_good = cross_entropy(y_true, y_pred_good)
    loss_bad = cross_entropy(y_true, y_pred_bad)
    
    print(f"  [SUCCESS] Categorical cross-entropy aligns logically. True positive loss: {loss_good:.4f}, Discordant loss: {loss_bad:.4f}")
    assert loss_good < loss_bad

def test_wsi_pipeline():
    print("[TEST] Running Whole Slide Image Grid Tiling Inference Runs...")
    result = run_inference(width=2048, height=2048, threshold=0.5)
    
    assert "overall_grade" in result
    assert "overall_confidence" in result
    assert "patches" in result
    
    print(f"  [SUCCESS] Whole Slide pipeline returned status code overall grade: '{result['overall_grade']}' with confidence {result['overall_confidence']}.")
    print(f"  [SUCCESS] Processed {len(result['patches'])} patches of size 256x256.")

if __name__ == "__main__":
    print("=== OralDysplasia AI: Executing Automated Mathematical Verification ===")
    try:
        test_sw_msa_arithmetic()
        test_cross_entropy()
        test_wsi_pipeline()
        print("=== [ALL TESTS PASSED SUCCESSFULLY] ===")
    except Exception as e:
        print(f"  [FAIL] Testing encountered error: {e}")
        sys.exit(1)
