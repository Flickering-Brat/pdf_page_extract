import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Printer", page_icon="⛽")

st.title("⛽ IOCL Smart Triple-Invoice Packer")
st.markdown("This version extracts your selected invoices and packs them **3-per-page** on A4 sheets for zero paper waste.")

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
                
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                third_h = height / 3

                # Define Top, Middle, Bottom coordinates
                sections = [
                    (0, third_h * 2, width, height), 
                    (0, third_h, width, third_h * 2),   
                    (0, 0, width, third_h)            
                ]

                for coords in sections:
                    # Temporary crop to check date
                    page.cropbox.lower_left = (coords[0], coords[1])
                    page.cropbox.upper_right = (coords[2], coords[3])
                    text = page.extract_text()
                    
                    if "Booking Date :" in text:
                        try:
                            date_part = text.split("Booking Date :")[1].strip()[:10]
                            curr_date = datetime.strptime(date_part, "%d-%m-%Y")

                            if start_date <= curr_date <= end_date:
                                # Create a standalone slip object
                                slip_writer = PyPDF2.PdfWriter()
                                slip_writer.add_page(page)
                                slip_page = slip_writer.pages[0]
                                
                                # Shift content to bottom
                                slip_page.add_transformation(PyPDF2.Transformation().translate(tx=0, ty=-coords[1]))
                                slip_page.mediabox.lower_left = (0, 0)
                                slip_page.mediabox.upper_right = (width, third_h)
                                
                                collected_slips.append((curr_date, slip_page))
                        except:
                            continue

            # Sort chronological
            collected_slips.sort(key=lambda x: x[0])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                # --- PACKING LOGIC: 3 Slips per 1 A4 Page ---
                for j in range(0, len(collected_slips), 3):
                    # Create a new blank A4 page (595 x 842 points)
                    new_a4 = final_writer.add_blank_page(width=595, height=842)
                    
                    # Get the batch of up to 3 slips
                    batch = collected_slips[j:j+3]
                    
                    for index, (dt, slip) in enumerate(batch):
                        # Calculate position: 0=Top, 1=Middle, 2=Bottom
                        y_offset = (2 - index) * (842 / 3)
                        
                        # Merge the slip onto the A4 page at the correct height
                        new_a4.merge_page(slip)
                        new_a4.add_transformation(PyPDF2.Transformation().translate(tx=0, ty=y_offset))

                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Success! Packed {len(collected_slips)} invoices onto {final_writer.get_num_pages()} A4 pages.")
                st.download_button(
                    label="📥 Download Packed A4 PDF",
                    data=output_pdf,
                    file_name=f"Packed_Invoices_{start_str}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("No invoices found.")

        except Exception as e:
            st.error(f"Error: {e}")
