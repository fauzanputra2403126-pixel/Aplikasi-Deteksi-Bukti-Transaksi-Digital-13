import numpy as np
from modules.template_generator import string_to_ascii_binary_vector, clean_nominal_string

def compute_forensic_hamming(vector_x, vector_y, ar_x, ar_y, nominal_tagihan, nominal_resi_ocr, ela_score, fg_threshold=65.0):
    """
    Mesin Keputusan Forensik Foreground-Only Hamming Engine:
    1. Metrik Biner ASCII String Nominal (d_ascii & wt_ascii)
    2. Metrik Biner Piksel TEKS Saja / Foreground (100% Membuang Latar Belakang Putih)
    3. Verifikasi Teorema Matematika: d(x,y) == wt(e)
    """
    str_x = clean_nominal_string(nominal_tagihan)
    str_y = clean_nominal_string(nominal_resi_ocr) if nominal_resi_ocr else str_x
    
    # -------------------------------------------------------------
    # 1. METRIK BINER ASCII STRING
    # -------------------------------------------------------------
    max_len = max(len(str_x), len(str_y), 1)
    str_x_pad = str_x.ljust(max_len, ' ')
    str_y_pad = str_y.ljust(max_len, ' ')
    
    vec_ascii_x = string_to_ascii_binary_vector(str_x_pad)
    vec_ascii_y = string_to_ascii_binary_vector(str_y_pad)
    
    err_ascii = np.bitwise_xor(vec_ascii_x, vec_ascii_y)
    hd_ascii = int(np.sum(err_ascii))
    hw_ascii = int(np.count_nonzero(err_ascii))
    
    # -------------------------------------------------------------
    # 2. METRIK BINER PIKSEL TEKS (FOREGROUND ONLY)
    # Membuang 100% Latar Belakang Putih dari Perhitungan
    # -------------------------------------------------------------
    fg_mask = (vector_x == 1) | (vector_y == 1)
    total_fg_pixels = int(np.sum(fg_mask))
    
    if total_fg_pixels == 0:
        fg_sim_ratio = 100.0
        hd_fg = 0
        hw_fg = 0
    else:
        err_fg = np.bitwise_xor(vector_x[fg_mask], vector_y[fg_mask])
        hd_fg = int(np.sum(err_fg))
        hw_fg = int(np.count_nonzero(err_fg))
        fg_sim_ratio = (1.0 - (hd_fg / total_fg_pixels)) * 100.0
        
    # -------------------------------------------------------------
    # 3. VERIFIKASI TEOREMA MATEMATIKA: d(x,y) == wt(e)
    # -------------------------------------------------------------
    is_verified = (hd_ascii == hw_ascii) and (hd_fg == hw_fg)
    
    # KONDISI KELULUSAN FORENSIK TEKS
    is_ascii_match = (hd_ascii == 0)
    is_fg_ok = (fg_sim_ratio >= fg_threshold)
    
    if is_ascii_match and is_fg_ok:
        verdict = "VALID_ASLI"
        title_output = "🟢 BUKTI TRANSAKSI INI ASLI"
        description = (
            f"Dokumen terverifikasi 100% VALID & ASLI. Nominal biner ASCII cocok sempurna "
            f"(ASCII Hamming Distance = 0 bit) dan kemiripan piksel TEKS INFORMASI PENTING (Foreground Similarity) "
            f"sebesar {fg_sim_ratio:.2f}% (memenuhi ambang batas {fg_threshold}%)."
        )
    else:
        verdict = "MANIPULASI_PALSU"
        title_output = "🔴 BUKTI TRANSAKSI INI PALSU"
        
        reasons = []
        if not is_ascii_match:
            reasons.append(f"Ketidakcocokan nominal biner ASCII (d_ascii = {hd_ascii} bit, Tagihan: Rp {int(str_x):,} vs Resi: Rp {str_y})")
        if not is_fg_ok:
            reasons.append(f"Kemiripan biner piksel teks informasi penting terlalu rendah ({fg_sim_ratio:.2f}% < {fg_threshold}%)")
            
        description = "TERINDIKASI MANIPULASI / PALSU! Alasan: " + " & ".join(reasons) + "."

    return {
        'total_bits_ascii': len(vec_ascii_x),
        'hd_ascii': hd_ascii,
        'hw_ascii': hw_ascii,
        'total_fg_pixels': total_fg_pixels,
        'hd_fg': hd_fg,
        'hw_fg': hw_fg,
        'fg_sim_ratio': fg_sim_ratio,
        'ela_score': ela_score,
        'is_verified': is_verified,
        'verdict': verdict,
        'title_output': title_output,
        'description': description
    }