import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Packer", page_icon="⛽")

st.title("⛽ IOCL Zero-Blank-Page Invoice Tool")
st.markdown("Fixes blank page issues by using physical boundary re-definition.")

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
                
                # Get actual page size from PDF
                # Standard A4 is roughly 595 x 842 points
                p_width = page.mediabox.width
                p_height = page.mediabox.height
                third_h = p_height / 3

                # Coordinates for Top, Middle, Bottom sections
                sections = [
                    (0, third_h * 2, p_width, p_height), # Top
                    (0, third_h, p_width, third_h * 2),   # Middle
                    (0, 0, p_width, third_h)              # Bottom
                ]

                for coords in sections:
                    # Create a clean page object
                    temp_writer = PyPDF2.PdfWriter()
                    temp_writer.add_page(page)
                    slip_page = temp_writer.pages[0]

                    # PHYSICAL EXTRACTION: Isolate the section for date checking
                    slip_page.mediabox.lower_left = (coords[0], coords[1])
                    slip_page.mediabox.upper_right = (coords[2], coords[3])
                    slip_page.cropbox.lower_left = (coords[0], coords[1])
                    slip_page.cropbox.upper_right = (coords[2], coords[3])
                    
                    text = slip_page.extract_text()
                    
                    if "Booking Date :" in text:
                        try:
                            # Parse date found in this 1/3rd section
                            date_part = text.split("Booking Date :")[1].strip()[:10]
                            curr_date = datetime.strptime(date_part, "%d-%m-%Y")

                            if start_date <= curr_date <= end_date:
                                # We store the 'isolated' slip page
                                # Note: It currently has its origin at its original y-coordinate
                                collected_slips.append({
                                    "date": curr_date,
                                    "page": page,
                                    "box": coords
                                })
                        except:
                            continue

            # Sort chronological
            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                final_writer = PyPDF2.PdfWriter()
                
                # Pack 3 invoices per A4 page
                for j in range(0, len(collected_slips), 3):
                    new_a4 = final_writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        # Calculate target position on new page
                        # index 0 -> Top, 1 -> Middle, 2 -> Bottom
                        target_y_bottom = (2 - index) * (842 / 3)
                        
                        # Use merge_page with a direct transformation to ensure visibility
                        # This moves the content from its original location (item["box"][1]) 
                        # to the target position on the blank A4
                        new_a4.merge_page(item["page"])
                        
                        # Create the transformation: Move it from original Y to 0, then to target Y
                        op = PyPDF2.Transformation().translate(tx=0, ty=-float(item["box"][1])).translate(tx=0, ty=target_y_bottom)
                        new_a4.add_transformation(op)
                        
                        # Apply a hard clip to prevent overlapping
                        new_a4.mediabox.lower_left = (0, 0)
                        new_a4.mediabox.upper_right = (595, 842)

                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Successfully packed {len(collected_slips)} invoices onto {len(final_writer.pages)} pages.")
                st.download_button(
                    label="📥 Download Corrected Packed PDF",
                    data=output_pdf,
                    file_name=f"Packed_Invoices_{start_str}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("No invoices found for the selected dates.")

        except Exception as e:
            st.error(f"Error: {e}")
