import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Packer", page_icon="⛽")

st.title("⛽ IOCL Zero-Blank-Page Packer")
st.markdown("This version uses **Absolute Positioning** to ensure invoices are never pushed off the page.")

uploaded_file = st.file_uploader("Upload 'Cash Memo Bulk.PDF'", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("End Date (DD-MM-YYYY)", "20-03-2026")

    if st.button("🚀 Generate Packed A4 PDF"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            reader = PyPDF2.PdfReader(uploaded_file)
            collected_slips = []
            
            progress_bar = st.progress(0)
            
            for i in range(len(reader.pages)):
                progress_bar.progress((i + 1) / len(reader.pages))
                page = reader.pages[i]
                
                # Standard A4 is 595x842
                p_width = float(page.mediabox.width)
                p_height = float(page.mediabox.height)
                third_h = p_height / 3

                # Define the three zones
                sections = [
                    (0, third_h * 2, p_width, p_height), # Top
                    (0, third_h, p_width, third_h * 2),   # Middle
                    (0, 0, p_width, third_h)              # Bottom
                ]

                for coords in sections:
                    # Create a copy of the page to isolate the slip
                    temp_writer = PyPDF2.PdfWriter()
                    temp_writer.add_page(page)
                    slip = temp_writer.pages[0]
                    
                    # Crop it to the specific slip area
                    slip.mediabox.lower_left = (coords[0], coords[1])
                    slip.mediabox.upper_right = (coords[2], coords[3])
                    slip.cropbox.lower_left = (coords[0], coords[1])
                    slip.cropbox.upper_right = (coords[2], coords[3])
                    
                    text = slip.extract_text()
                    
                    if "Booking Date :" in text:
                        try:
                            date_part = text.split("Booking Date :")[1].strip()[:10]
                            curr_date = datetime.strptime(date_part, "%d-%m-%Y")

                            if start_date <= curr_date <= end_date:
                                # We store the data we need to rebuild the page
                                collected_slips.append({
                                    "date": curr_date,
                                    "original_page": page,
                                    "source_box": coords
                                })
                        except:
                            continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                # Pack 3 invoices per A4 page
                for j in range(0, len(collected_slips), 3):
                    # Create a blank A4 sheet
                    new_page = final_writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        # Target height for each slip on the new A4
                        target_h = 842 / 3
                        # target_y: 0=Top(561), 1=Mid(280), 2=Bot(0)
                        target_y = (2 - index) * target_h
                        
                        # Use merge_transformed_page for absolute control
                        # This moves the specific part of the original page to our new slot
                        translation = PyPDF2.Transformation().translate(
                            tx=0, 
                            ty=target_y - item["source_box"][1]
                        )
                        
                        new_page.merge_transformed_page(item["original_page"], translation)
                    
                    # Final safety check on boundaries
                    new_page.mediabox.lower_left = (0, 0)
                    new_page.mediabox.upper_right = (595, 842)

                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Packed {len(collected_slips)} invoices onto {len(final_writer.pages)} pages.")
                st.download_button("📥 Download Corrected PDF", output_pdf, f"Packed_Invoices.pdf", "application/pdf")
            else:
                st.error("No invoices found for these dates.")
        except Exception as e:
            st.error(f"Error: {e}")
