import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Light-PDF Tool", page_icon="⚡")

st.title("⚡ IOCL Fast-Download Invoice Tool")
st.markdown("This version uses **Object Isolation** to reduce file size for slow internet connections.")

uploaded_file = st.file_uploader("Upload Bulk PDF", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("End Date (DD-MM-YYYY)", "20-03-2026")

    if st.button("🚀 Generate Lightweight PDF"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            reader = PyPDF2.PdfReader(uploaded_file)
            collected_invoices = []
            
            progress_bar = st.progress(0)
            
            for i in range(len(reader.pages)):
                progress_bar.progress((i + 1) / len(reader.pages))
                page = reader.pages[i]
                
                # Standard A4 dimensions
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
                    # Check text specifically in this 1/3rd area
                    page.cropbox.lower_left = (coords[0], coords[1])
                    page.cropbox.upper_right = (coords[2], coords[3])
                    text = page.extract_text()
                    
                    if "Booking Date :" in text:
                        try:
                            date_part = text.split("Booking Date :")[1].strip()[:10]
                            curr_date = datetime.strptime(date_part, "%d-%m-%Y")

                            if start_date <= curr_date <= end_date:
                                # --- THE LIGHTWEIGHT TRICK ---
                                # Create a fresh writer to 'clean' the page
                                cleaner_writer = PyPDF2.PdfWriter()
                                cleaner_writer.add_page(page)
                                clean_slip = cleaner_writer.pages[0]

                                # Shift content to bottom-left to remove white space
                                clean_slip.add_transformation(PyPDF2.Transformation().translate(tx=0, ty=-coords[1]))
                                
                                # Physically set dimensions to 1/3rd A4
                                clean_slip.mediabox.lower_left = (0, 0)
                                clean_slip.mediabox.upper_right = (width, third_h)
                                
                                # Compress content stream
                                clean_slip.compress_content_streams()
                                
                                collected_invoices.append((curr_date, clean_slip))
                        except:
                            continue

            # Sort results
            collected_invoices.sort(key=lambda x: x[0])

            if collected_invoices:
                final_writer = PyPDF2.PdfWriter()
                for _, p in collected_invoices:
                    final_writer.add_page(p)
                
                # Apply global compression
                final_writer.add_metadata({"/Producer": "IOCL-Light-Tool"})
                
                output_pdf = io.BytesIO()
                final_writer.write(output_pdf)
                output_pdf.seek(0)

                st.success(f"Generated {len(collected_invoices)} invoices. Download ready!")
                st.download_button(
                    label="📥 Download Fast-PDF",
                    data=output_pdf,
                    file_name=f"Light_Invoices_{start_str}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("No invoices found for these dates.")

        except Exception as e:
            st.error(f"Error: {e}")
