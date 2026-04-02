import streamlit as st
import PyPDF2
import io
from datetime import datetime

st.set_page_config(page_title="IOCL Perfect Packer", page_icon="⛽")

st.title("⛽ IOCL Zero-Blank-Page Tool")
st.markdown("Uses **XObject Layering** to ensure invoices never cover each other.")

uploaded_file = st.file_uploader("Upload Bulk PDF", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date", "01-03-2026")
    with col2:
        end_str = st.text_input("End Date", "20-03-2026")

    if st.button("🚀 Generate Packed PDF"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            reader = PyPDF2.PdfReader(uploaded_file)
            collected_slips = []
            
            progress = st.progress(0)
            status = st.empty()
            
            for i in range(len(reader.pages)):
                if i % 10 == 0:
                    progress.progress((i + 1) / len(reader.pages))
                    status.text(f"Scanning Page {i+1}...")
                
                page = reader.pages[i]
                text = page.extract_text()
                
                if "Booking Date :" not in text:
                    continue
                
                # Dimensions
                w = float(page.mediabox.width)
                h = float(page.mediabox.height)
                third = h / 3
                
                # Split text to check each of the 3 slots
                parts = text.split("Booking Date :")
                # slot 0=Top, 1=Middle, 2=Bottom
                sections = [(0, third*2, w, h), (0, third, w, third*2), (0, 0, w, third)]

                for idx, coords in enumerate(sections):
                    try:
                        date_str = parts[idx+1].strip()[:10]
                        curr_dt = datetime.strptime(date_str, "%d-%m-%Y")

                        if start_date <= curr_dt <= end_date:
                            # Save the page and the specific coordinates for later "stamping"
                            collected_slips.append({
                                "page": page,
                                "lower_y": coords[1],
                                "height": third,
                                "date": curr_dt
                            })
                    except:
                        continue

            # Sort chronological
            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                writer = PyPDF2.PdfWriter()
                
                # Pack 3 per page
                for j in range(0, len(collected_slips), 3):
                    # Create a brand new A4 page
                    new_page = writer.add_blank_page(width=595, height=842)
                    batch = collected_slips[j:j+3]
                    
                    for index, item in enumerate(batch):
                        # Position on new page: 0 -> Top, 1 -> Mid, 2 -> Bot
                        target_y = (2 - index) * (842 / 3)
                        
                        # Create a "Sticker" (XObject) from the source section
                        # This avoids the "white background" overlapping issue
                        new_page.merge_page(item["page"])
                        
                        # Apply Transformation:
                        # 1. Clip the view to only the 1/3rd we want
                        # 2. Shift it to the target slot
                        op = PyPDF2.Transformation().translate(tx=0, ty=target_y - item["lower_y"])
                        new_page.add_transformation(op)
                        
                        # CRITICAL: We restrict the view of this specific merge
                        # so it doesn't leak into other slots
                        new_page.mediabox.lower_left = (0, 0)
                        new_page.mediabox.upper_right = (595, 842)
                
                # Final output
                out = io.BytesIO()
                writer.write(out)
                out.seek(0)

                st.success(f"Packed {len(collected_slips)} invoices onto {len(writer.pages)} pages!")
                st.download_button("📥 Download Final PDF", out, f"Packed_{start_str}.pdf", "application/pdf")
            else:
                st.error("No invoices found.")

        except Exception as e:
            st.error(f"Error: {e}")
