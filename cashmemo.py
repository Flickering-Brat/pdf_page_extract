import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Fast Packer", page_icon="⚡")

st.title("⚡ IOCL High-Speed Invoice Packer")
st.markdown("Optimized for 500+ pages. This version scans and packs invoices much faster.")

uploaded_file = st.file_uploader("Upload 'Cash Memo Bulk.PDF'", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("End Date (DD-MM-YYYY)", "20-03-2026")

    if st.button("🚀 Fast Generate Packed PDF"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            reader = PyPDF2.PdfReader(uploaded_file)
            collected_slips = []
            
            progress_bar = st.progress(0)
            status = st.empty()
            
            total_pages = len(reader.pages)

            for i in range(total_pages):
                if i % 10 == 0:
                    progress_bar.progress((i + 1) / total_pages)
                    status.text(f"Scanning page {i+1} of {total_pages}...")
                
                page = reader.pages[i]
                full_text = page.extract_text()
                
                # High-speed check: Does the page even have the date label?
                if "Booking Date :" not in full_text:
                    continue
                
                p_width = float(page.mediabox.width)
                p_height = float(page.mediabox.height)
                third_h = p_height / 3

                # Define the 3 vertical section boundaries
                sections = [
                    (0, third_h * 2, p_width, p_height), # Top
                    (0, third_h, p_width, third_h * 2),   # Middle
                    (0, 0, p_width, third_h)              # Bottom
                ]

                # Split the text by the label to find individual dates on the page
                parts = full_text.split("Booking Date :")
                
                for idx, coords in enumerate(sections):
                    # We check if the text for this specific section contains a valid date
                    # This is faster than re-extracting text 3 times per page
                    try:
                        # Extract the date string following the 'Booking Date :' label
                        date_str = parts[idx+1].strip()[:10]
                        curr_date = datetime.strptime(date_str, "%d-%m-%Y")

                        if start_date <= curr_date <= end_date:
                            # Only perform the expensive PDF operations for matched dates
                            collected_slips.append({
                                "date": curr_date,
                                "page_index": i,
                                "box": coords
                            })
                    except:
                        continue

            # Sort chronological
            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                for j in range(0, len(collected_slips), 3):
                    new_a4 = final_writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        source_page = reader.pages[item["page_index"]]
                        
                        # Calculate target position (Top, Middle, Bottom)
                        target_y = (2 - index) * (842 / 3)
                        
                        # Merge the original page
                        new_a4.merge_page(source_page)
                        
                        # Transform: Shift the specific 1/3rd section into view
                        # We move the content so that item["box"][1] aligns with target_y
                        diff = target_y - item["box"][1]
                        new_a4.add_transformation(PyPDF2.Transformation().translate(tx=0, ty=diff))
                        
                        # Clip the page boundaries
                        new_a4.mediabox.lower_left = (0, 0)
                        new_a4.mediabox.upper_right = (595, 842)

                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Success! Processed {total_pages} pages. Found {len(collected_slips)} invoices.")
                st.download_button("📥 Download Packed PDF", output_pdf, f"Packed_Invoices_{start_str}.pdf", "application/pdf")
            else:
                st.error("No invoices found for the selected dates.")

        except Exception as e:
            st.error(f"Error: {e}")
