import html
import random
from datetime import datetime, timedelta, timezone
from math import floor

import streamlit as st

st.set_page_config(page_title="Guntur Spice Kitchen - Billing", page_icon="🧾", layout="centered")

# ------------------------------------------------------------------
# Restaurant details (sample / fictional - edit as you like)
# ------------------------------------------------------------------
RESTAURANT = {
    "name": "GUNTUR SPICE KITCHEN",
    "tagline": "Authentic Andhra Flavours",
    "address": "Brodipet, Guntur - 522002, Andhra Pradesh",
    "phone": "0863-2XXXXXX",
    "gstin": "37ABCDE1234F1Z5",  # sample GSTIN (37 = Andhra Pradesh state code)
}
IST = timezone(timedelta(hours=5, minutes=30))  # Streamlit Cloud runs on UTC, so we convert to IST

GST_RATE = 0.05        # 5% GST for restaurants (CGST 2.5% + SGST 2.5%)
SERVICE_RATE = 0.05    # optional service charge
PACKING_CHARGE = 20.0  # flat packing charge for takeaway

# ------------------------------------------------------------------
# Menu: mid-range Guntur-style prices in Rs (edit freely)
# ------------------------------------------------------------------
MENU = {
    "🍳 Tiffins": {
        "Idli (2 pcs)": 50, "Vada (2 pcs)": 50, "Plain Dosa": 60, "Masala Dosa": 80,
        "Ghee Karam Dosa": 90, "Pesarattu (Upma)": 90, "Poori (3 pcs)": 70,
    },
    "🥗 Veg Starters": {
        "Gobi 65": 160, "Paneer 65": 180, "Chilli Gobi": 140, "Chilli Paneer": 180,
        "Veg Manchurian": 160, "Baby Corn Manchurian": 170, "French Fries": 170,
    },
    "🍗 Non-Veg Starters": {
        "Chicken 65": 240, "Andhra Chicken Fry": 260, "Chilli Chicken": 250,
        "Chicken Lollipop (6 pcs)": 260, "Apollo Fish": 300, "Chicken Tikka": 440,
        "Tandoori Chicken (Half)": 420, "Chicken Tangdi Kebab": 420, "Tandoori Chicken (Full)": 700,
    },
    "🍛 Biryani & Rice": {
        "Veg Biryani": 180, "Egg Biryani": 200, "Paneer Biryani": 230, "Chicken Dum Biryani": 260,
        "Guntur Special Chicken Biryani": 280, "Gongura Chicken Biryani": 290,
        "Prawns Biryani": 340, "Mutton Biryani": 360, "Family Pack Chicken Biryani": 720,
        "Curd Rice": 80, "Jeera Rice": 140,
    },
    "🍽️ Andhra Meals": {
        "Veg Meals": 150, "Non-Veg Meals": 230, "Fish Meals": 260, "Special Mutton Meals": 320,
    },
    "🍲 Curries": {
        "Andhra Chicken Curry": 240, "Gongura Chicken": 270, "Mutton Curry": 330,
        "Gongura Mutton": 340, "Chepala Pulusu (Fish)": 280, "Paneer Butter Masala": 220,
        "Gutti Vankaya Curry": 170, "Dal Tadka": 150,
    },
    "🫓 Breads": {
        "Chapati": 25, "Kerala Parotta": 35, "Tandoori Roti": 30, "Plain Naan": 40,
        "Butter Naan": 50, "Kulcha": 55,
    },
    "🥤 Desserts & Drinks": {
        "Gulab Jamun (2 pcs)": 70, "Double Ka Meetha": 90, "Ice Cream Scoop": 70,
        "Butter Milk": 30, "Tea": 20, "Filter Coffee": 30, "Soft Drink": 40,
        "Fresh Lime Soda": 60, "Sweet Lassi": 80, "Banana Milkshake": 115,
    },
}
PRICES = {item: price for items in MENU.values() for item, price in items.items()}
assert len(PRICES) == sum(len(v) for v in MENU.values()), "Duplicate item names in MENU"

PRESETS = {
    "👨‍👩‍👧‍👦 Family lunch (4)": {"Gobi 65": 1, "Chicken 65": 1, "Chicken Dum Biryani": 2,
                               "Mutton Biryani": 1, "Butter Naan": 2, "Soft Drink": 4},
    "☕ Tiffin breakfast (2)": {"Idli (2 pcs)": 2, "Ghee Karam Dosa": 1, "Pesarattu (Upma)": 1,
                              "Vada (2 pcs)": 1, "Filter Coffee": 2},
    "🍽️ Andhra meals (2)": {"Non-Veg Meals": 1, "Veg Meals": 1, "Butter Milk": 2},
}


# ------------------------------------------------------------------
# Logic
# ------------------------------------------------------------------
def money(x: float) -> str:
    return f"₹{x:,.2f}"


def calculate_bill(subtotal, discount_pct=0, service=False, packing=False) -> dict:
    """Food total -> discount -> service/packing -> CGST+SGST -> round off -> grand total."""
    discount = round(subtotal * discount_pct / 100, 2)
    after_discount = round(subtotal - discount, 2)
    service_charge = round(after_discount * SERVICE_RATE, 2) if service else 0.0
    packing_charge = PACKING_CHARGE if packing else 0.0
    taxable = round(after_discount + service_charge + packing_charge, 2)
    cgst = round(taxable * GST_RATE / 2, 2)
    sgst = cgst
    total = round(taxable + cgst + sgst, 2)
    grand_total = floor(total + 0.5)          # round to nearest rupee (.50 rounds up)
    round_off = round(grand_total - total, 2)
    return {"subtotal": subtotal, "discount": discount, "service": service_charge,
            "packing": packing_charge, "taxable": taxable, "cgst": cgst, "sgst": sgst,
            "round_off": round_off, "grand_total": grand_total}


def new_bill_number() -> str:
    return f"GSK{datetime.now(IST):%y%m%d}-{random.randint(1000, 9999)}"


def clear_order():
    for item in PRICES:
        st.session_state[f"qty_{item}"] = 0


def load_preset(name):
    clear_order()
    for item, qty in PRESETS[name].items():
        st.session_state[f"qty_{item}"] = qty


def start_new_bill():
    clear_order()
    st.session_state.update(bill_no=new_bill_number(), bill_time=datetime.now(IST),
                            customer="", phone="")


def signed(x: float) -> str:
    return ("+" if x >= 0 else "-") + money(abs(x))


def receipt_text(info, order, b) -> str:
    w = 44
    lines = [RESTAURANT["name"].center(w), RESTAURANT["address"].center(w),
             f"GSTIN: {RESTAURANT['gstin']}".center(w), "=" * w,
             f"Bill No : {info['bill_no']}", f"Date    : {info['when']:%d-%m-%Y %I:%M %p}",
             f"Type    : {info['order_type']}   Table: {info['table']}",
             f"Customer: {info['customer'] or 'Guest'}", "-" * w,
             f"{'Item':<20}{'Rate':>7}{'Qty':>5}{'Amount':>12}", "-" * w]
    for r in order:
        lines.append(f"{r['name'][:19]:<20}{r['rate']:>7}{r['qty']:>5}{r['amount']:>12,.2f}")
    lines += ["-" * w, f"{'Sub Total':<32}{b['subtotal']:>12,.2f}"]
    if b["discount"]:
        lines.append(f"{'Discount':<32}{-b['discount']:>12,.2f}")
    if b["service"]:
        lines.append(f"{'Service Charge (5%)':<32}{b['service']:>12,.2f}")
    if b["packing"]:
        lines.append(f"{'Packing Charge':<32}{b['packing']:>12,.2f}")
    lines += [f"{'CGST @ 2.5%':<32}{b['cgst']:>12,.2f}", f"{'SGST @ 2.5%':<32}{b['sgst']:>12,.2f}",
              f"{'Round Off':<32}{b['round_off']:>+12,.2f}", "=" * w,
              f"{'GRAND TOTAL':<28}Rs.{b['grand_total']:>10,.2f}", "=" * w,
              f"Paid by: {info['payment']}", "Thank you! Visit again.".center(w)]
    return "\n".join(lines)


def receipt_html(info, order, b) -> str:
    td = "padding:2px 4px;"
    rows = "".join(
        f"<tr><td style='{td}'>{html.escape(r['name'])}</td>"
        f"<td style='{td}text-align:right'>{r['rate']}</td>"
        f"<td style='{td}text-align:center'>{r['qty']}</td>"
        f"<td style='{td}text-align:right'>{r['amount']:,.2f}</td></tr>" for r in order)

    def line(label, value, bold=False):
        weight = "font-weight:700;" if bold else ""
        return (f"<tr style='{weight}'><td colspan='3' style='{td}'>{label}</td>"
                f"<td style='{td}text-align:right'>{value}</td></tr>")

    extra = line("Sub Total", f"{b['subtotal']:,.2f}")
    if b["discount"]:
        extra += line("Discount", f"-{b['discount']:,.2f}")
    if b["service"]:
        extra += line("Service Charge (5%)", f"{b['service']:,.2f}")
    if b["packing"]:
        extra += line("Packing Charge", f"{b['packing']:,.2f}")
    extra += line("CGST @ 2.5%", f"{b['cgst']:,.2f}") + line("SGST @ 2.5%", f"{b['sgst']:,.2f}")
    extra += line("Round Off", f"{b['round_off']:+,.2f}")
    dash = "<hr style='border:none;border-top:1px dashed #555;margin:8px 0'>"
    return (
        "<div style=\"background:#fffdf5;color:#222;border:1px solid #d9d2bd;border-radius:8px;"
        "padding:16px;font-family:'Courier New',monospace;font-size:14px;max-width:520px;margin:auto\">"
        f"<div style='text-align:center'><div style='font-size:18px;font-weight:700'>{RESTAURANT['name']}</div>"
        f"<div>{RESTAURANT['tagline']}</div><div>{RESTAURANT['address']}</div>"
        f"<div>Ph: {RESTAURANT['phone']}</div><div>GSTIN: {RESTAURANT['gstin']}</div></div>{dash}"
        f"<div>Bill No : <b>{info['bill_no']}</b></div>"
        f"<div>Date    : {info['when']:%d-%m-%Y %I:%M %p}</div>"
        f"<div>Type    : {info['order_type']} &nbsp; Table: {info['table']}</div>"
        f"<div>Customer: {html.escape(info['customer'] or 'Guest')}</div>"
        f"<div>Served by: {info['server']}</div>{dash}"
        "<table style='width:100%;border-collapse:collapse;color:#222'>"
        "<tr style='border-bottom:1px dashed #555'><th style='text-align:left'>Item</th>"
        "<th style='text-align:right'>Rate</th><th>Qty</th><th style='text-align:right'>Amount</th></tr>"
        f"{rows}</table>{dash}<table style='width:100%;border-collapse:collapse;color:#222'>{extra}</table>{dash}"
        "<table style='width:100%;color:#222'><tr style='font-size:18px;font-weight:700'>"
        f"<td>GRAND TOTAL</td><td style='text-align:right'>₹{b['grand_total']:,.2f}</td></tr></table>{dash}"
        f"<div>Paid by: {info['payment']}</div>"
        "<div style='text-align:center;margin-top:8px'>Thank you! Visit again 🙏</div></div>"
    )


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
if "bill_no" not in st.session_state:
    st.session_state.bill_no = new_bill_number()
    st.session_state.bill_time = datetime.now(IST)

st.title("🧾 Restaurant Billing")
st.caption(f"{RESTAURANT['name'].title()} • {RESTAURANT['address']}")

st.subheader("1️⃣ Order details")
c1, c2 = st.columns(2)
order_type = c1.radio("Order type", ["Dine-in", "Takeaway"], horizontal=True, key="order_type")
table_no = c2.number_input("Table no.", min_value=1, max_value=40, value=1, key="table",
                           disabled=(order_type == "Takeaway"))
c3, c4 = st.columns(2)
customer = c3.text_input("Customer name (optional)", key="customer")
server = c4.selectbox("Served by", ["Ravi", "Suresh", "Lakshmi", "Naveen"], key="server")

st.subheader("2️⃣ Add items")
st.caption("Quick demo orders:")
pc = st.columns(len(PRESETS))
for i, name in enumerate(PRESETS):
    pc[i].button(name, key=f"preset_{i}", on_click=load_preset, args=(name,), width="stretch")

tabs = st.tabs(list(MENU))
for tab, (category, items) in zip(tabs, MENU.items()):
    with tab:
        for item, price in items.items():
            st.number_input(f"{item} — ₹{price}", min_value=0, max_value=50, step=1, key=f"qty_{item}")

order = [{"name": n, "rate": p, "qty": st.session_state.get(f"qty_{n}", 0),
          "amount": p * st.session_state.get(f"qty_{n}", 0)}
         for n, p in PRICES.items() if st.session_state.get(f"qty_{n}", 0) > 0]

st.subheader("3️⃣ Bill options")
o1, o2 = st.columns(2)
discount_pct = o1.selectbox("Discount", [0, 5, 10, 15, 20], format_func=lambda d: "No discount" if d == 0 else f"{d}% off",
                            key="discount_pct")
payment = o2.selectbox("Payment mode", ["Cash", "UPI", "Card"], key="payment")
service_on = st.checkbox("Add service charge (5%) — optional", key="service")
st.caption(f"GST 5% (CGST 2.5% + SGST 2.5%) is added automatically. "
           f"{'Packing charge ₹20 applies for takeaway.' if order_type == 'Takeaway' else ''}")

st.subheader("4️⃣ Final bill")
if not order:
    st.info("No items yet. Choose a demo order above or add items from the menu tabs 👆")
else:
    subtotal = float(sum(r["amount"] for r in order))
    bill = calculate_bill(subtotal, discount_pct, service_on, order_type == "Takeaway")
    info = {"bill_no": st.session_state.bill_no, "when": st.session_state.bill_time,
            "order_type": order_type, "table": table_no if order_type == "Dine-in" else "-",
            "customer": customer.strip(), "server": server, "payment": payment}
    st.markdown(receipt_html(info, order, bill), unsafe_allow_html=True)
    st.metric("Amount Payable", f"₹{bill['grand_total']:,}")
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download bill (.txt)", receipt_text(info, order, bill),
                       file_name=f"{info['bill_no']}.txt", width="stretch")
    d2.button("🆕 New bill", on_click=start_new_bill, width="stretch")
