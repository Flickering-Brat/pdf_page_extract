import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Packer", page_icon="⛽")

st.title("⛽ IOCL High-Speed Invoice Packer")
st.markdown("Monitor real-time scanning and invoice extraction below.")

uploaded_file = st.file_uploader("Upload 'Cash Memo Bulk.PDF'", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("To Date (DD-MM-YYYY)", "20-03-2026")

    if st.button("🚀 Start Extraction"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            reader = PyPDF2.PdfReader(uploaded_file)
            total_pages = len(reader.pages)
            collected_slips = []
            
            # --- PROGRESS ELEMENTS ---
            progress_bar = st.progress(0)
            progress_text = st.empty()
            log_container = st.expander("Detailed Operation Log", expanded=True)
            log_text = ""

            for i in range(total_pages):
                # Update progress counter (e.g., 1 of 465)
                current_progress = (i + 1) / total_pages
                progress_bar.progress(current_progress)
                progress_text.text(f"Scanning page {i+1} of {total_pages}...")

                page = reader.pages[i]
                full_text = page.extract_text()
                
                if "Booking Date :" not in full_text:
                    continue
                
                p_width = float(page.mediabox.width)
                p_height = float(page.mediabox.height)
                third_h = p_height / 3
                
                # Top, Middle, Bottom coordinates
                sections = [
                    (0, third_h * 2, p_width, p_height),
                    (0, third_h, p_width, third_h * 2),
                    (0, 0, p_width, third_h)
                ]

                parts = full_text.split("Booking Date :")
                
                for idx, coords in enumerate(sections):
                    try:
                        date_str = parts[idx+1].strip()[:10]
                        curr_date = datetime.strptime(date_str, "%d-%m-%Y")

                        if start_date <= curr_date <= end_date:
                            collected_slips.append({
                                "date": curr_date,
                                "original_page": page,
                                "source_box": coords
                            })
                            # Show "Invoice found on page X"
                            log_text += f"✅ Page {i+1}: Found invoice for {date_str}\n"
                            log_container.text(log_text)
                    except:
                        continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                for j in range(0, len(collected_slips), 3):
                    new_page = final_writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        target_y = (2 - index) * (842 / 3)
                        translation = PyPDF2.Transformation().translate(
                            tx=0, 
                            ty=target_y - item["source_box"][1]
                        )
                        new_page.merge_transformed_page(item["original_page"], translation)
                
                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Task Complete! Packed {len(collected_slips)} invoices onto {len(final_writer.pages)} pages.")
                st.download_button("📥 Download Final PDF", output_pdf, f"Packed_Invoices.pdf", "application/pdf")
            else:
                st.error("No invoices found for the selected dates.")
        except Exception as e:
            st.error(f"Error: {e}")
