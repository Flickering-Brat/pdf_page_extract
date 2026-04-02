import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Packer", page_icon="⛽")

st.title("⛽ IOCL High-Speed Invoice Packer")
st.markdown("Real-time extraction and 3-per-page A4 packing.")

uploaded_file = st.file_uploader("Upload Bulk PDF", type="pdf")

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
            
            # Progress Monitoring
            progress_bar = st.progress(0)
            progress_text = st.empty()
            log_container = st.expander("Operation Log", expanded=True)
            log_entries = []

            for i in range(total_pages):
                # Update visual counter (e.g., 1 of 465)
                progress_bar.progress((i + 1) / total_pages)
                progress_text.text(f"Scanning page {i+1} of {total_pages}...")

                page = reader.pages[i]
                full_text = page.extract_text()
                
                if "Booking Date :" not in full_text:
                    continue
                
                p_width = float(page.mediabox.width)
                p_height = float(page.mediabox.height)
                third_h = p_height / 3
                
                sections = [
                    (0, third_h * 2, p_width, p_height), # Top
                    (0, third_h, p_width, third_h * 2),   # Middle
                    (0, 0, p_width, third_h)              # Bottom
                ]

                parts = full_text.split("Booking Date :")
                
                for idx, coords in enumerate(sections):
                    try:
                        date_str = parts[idx+1].strip()[:10]
                        curr_date = datetime.strptime(date_str, "%d-%m-%Y")

                        if start_date <= curr_date <= end_date:
                            collected_slips.append({
                                "date": curr_date,
                                "page_index": i,
                                "source_y": coords[1]
                            })
                            log_entries.append(f"✅ Page {i+1}: Invoice found for {date_str}")
                            log_container.text("\n".join(log_entries[-10:])) # Show last 10 finds
                    except:
                        continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                for j in range(0, len(collected_slips), 3):
                    new_page = final_writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        # Create a fresh copy of the original page
                        source_page = reader.pages[item["page_index"]]
                        
                        # Calculate target position (0=Top, 1=Middle, 2=Bottom)
                        target_y = (2 - index) * (842 / 3)
                        
                        # Apply transformation to a temporary page object
                        # This avoids the 'merge_transformed_page' error
                        op = PyPDF2.Transformation().translate(tx=0, ty=target_y - item["source_y"])
                        
                        # Merge page and then apply the shift
                        new_page.merge_page(source_page)
                        new_page.add_transformation(op)
                    
                    # Lock the page view to A4 only
                    new_page.mediabox.lower_left = (0, 0)
                    new_page.mediabox.upper_right = (595, 842)

                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Task Complete! Packed {len(collected_slips)} invoices onto {len(final_writer.pages)} pages.")
                st.download_button("📥 Download Final PDF", output_pdf, f"Packed_Invoices.pdf", "application/pdf")
            else:
                st.error("No invoices found for the selected dates.")
        except Exception as e:
            st.error(f"Error: {e}")
