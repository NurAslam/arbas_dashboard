import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Arbas Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('./customers.csv')

    # Convert createdAt to datetime
    df['createdAt'] = pd.to_datetime(df['createdAt'], format='mixed', errors='coerce')

    # Convert contract dates
    df['awalKontrak'] = pd.to_datetime(df['awalKontrak'])
    df['akhirKontrak'] = pd.to_datetime(df['akhirKontrak'])

    # Extract region from alamat or kota column
    def extract_region(row):
        alamat = str(row['alamat']).lower() if pd.notna(row['alamat']) else ''
        kota = str(row['kota']).lower() if pd.notna(row['kota']) else ''

        if 'bantul' in alamat or 'bantul' in kota:
            return 'Bantul'
        elif 'sleman' in alamat or 'sleman' in kota:
            return 'Sleman'
        elif 'yogyakarta' in alamat or 'jogja' in alamat or 'yogyakarta' in kota:
            return 'Kota Yogyakarta'
        elif 'kulon progo' in alamat or 'kulonprogo' in kota:
            return 'Kulon Progo'
        elif 'gunung kidul' in alamat or 'gunungkidul' in kota:
            return 'Gunung Kidul'
        else:
            return 'Lainnya'

    df['daerah'] = df.apply(extract_region, axis=1)

    # Calculate contract duration in days
    df['durasiKontrak'] = (df['akhirKontrak'] - df['awalKontrak']).dt.days

    # Normalize status
    df['status'] = df['status'].str.strip().str.title()

    return df

df = load_data()

# Calculate reference date (today)
today = datetime.now()

# Sidebar filters
st.sidebar.header("🔍 Filter Data")

# Date range selector
date_filter = st.sidebar.radio(
    "Pilih Periode Data Baru:",
    ["30 Hari Terakhir", "60 Hari Terakhir", "90 Hari Terakhir", "Semua Data"]
)

# Calculate cutoff date
if date_filter == "20 Hari Terakhir":
    cutoff_date = today - timedelta(days=20)
elif date_filter == "30 Hari Terakhir":
    cutoff_date = today - timedelta(days=30)
elif date_filter == "60 Hari Terakhir":
    cutoff_date = today - timedelta(days=60)
else:
    cutoff_date = datetime.min

# Filter data
df_filtered = df[df['createdAt'] >= cutoff_date].copy()
end_date = df_filtered['createdAt'].max()
start_date = df_filtered['createdAt'].min()

start_date_fmt = start_date.strftime("%d %B %Y")
end_date_fmt = end_date.strftime("%d %B %Y")

st.sidebar.markdown(f"""
📅 **Periode Data**
- Dari: **{start_date_fmt}**
- Sampai: **{end_date_fmt}**
""")

# Display selected period info
st.sidebar.info(f"📅 Periode: {date_filter}")
st.sidebar.info(f"📊 Data: {len(df_filtered)} dari {len(df)} total")

# Additional filters
show_active_only = st.sidebar.checkbox("Hanya Aktif", value=True)
if show_active_only:
    df_filtered = df_filtered[df_filtered['status'] == 'Active']

# Main Header
st.markdown('<div class="main-header">📊 Arbas Data Dashboard</div>', unsafe_allow_html=True)
st.markdown(f"**Analisis Karakteristik Data Baru** - {date_filter}")
st.markdown("---")

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Customer Baru",
        value=f"{len(df_filtered):,}",
        delta=None
    )

with col2:
    active_count = len(df_filtered[df_filtered['status'] == 'Active'])
    st.metric(
        label="Customer Aktif",
        value=f"{active_count:,}",
        delta=None
    )

with col3:
    unique_regions = df_filtered['daerah'].nunique()
    st.metric(
        label="Total Daerah",
        value=f"{unique_regions}",
        delta=None
    )

with col4:
    unique_channels = df_filtered['tipeChannel'].nunique()
    st.metric(
        label="Tipe Channel",
        value=f"{unique_channels}",
        delta=None
    )

st.markdown("---")

# Tab 1: Overview & Tabel Data
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Tabel Data",
    "🗺️ Analisis Wilayah",
    "📊 Tipe Channel",
    "📅 Kontrak & Status",
    "🔗 Korelasi & Insight"
])

with tab1:
    st.subheader("Tabel Data Customer Baru")

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📍 **Daerah Terbanyak:** {df_filtered['daerah'].value_counts().index[0]}")
    with col2:
        st.info(f"🏪 **Channel Terbanyak:** {df_filtered['tipeChannel'].value_counts().index[0]}")
    with col3:
        st.info(f"✅ **Status Dominan:** {df_filtered['status'].value_counts().index[0]}")

    # Display table with selected columns
    display_columns = [
        'nama', 'type', 'alamat', 'daerah', 'tipeChannel',
        'awalKontrak', 'akhirKontrak', 'durasiKontrak', 'status', 'createdAt'
    ]

    df_display = df_filtered[display_columns].copy()
    df_display.columns = [
        'Nama', 'Type', 'Alamat', 'Daerah', 'Tipe Channel',
        'Awal Kontrak', 'Akhir Kontrak', 'Durasi (Hari)', 'Status', 'Tanggal Dibuat'
    ]

    # Search and filter
    search = st.text_input("🔍 Cari nama atau alamat:")
    if search:
        mask = df_display['Nama'].str.contains(search, case=False, na=False) | \
               df_display['Alamat'].str.contains(search, case=False, na=False)
        df_display = df_display[mask]

    st.dataframe(
        df_display.sort_values('Tanggal Dibuat', ascending=False),
        use_container_width=True,
        height=400
    )

    # Download button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data sebagai CSV",
        data=csv,
        file_name=f"customer_baru_{date_filter.replace(' ', '_')}.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("Analisis Berdasarkan Wilayah")

    col1, col2 = st.columns(2)

    with col1:
        # Pie chart distribusi daerah
        fig_region = px.pie(
            df_filtered,
            names='daerah',
            title='Distribusi Customer per Daerah',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig_region.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_region, use_container_width=True)

    with col2:
        # Bar chart daerah
        region_counts = df_filtered['daerah'].value_counts().reset_index()
        region_counts.columns = ['Daerah', 'Jumlah']

        fig_region_bar = px.bar(
            region_counts,
            x='Daerah',
            y='Jumlah',
            title='Jumlah Customer per Daerah',
            color='Jumlah',
            color_continuous_scale='Viridis'
        )
        fig_region_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_region_bar, use_container_width=True)

    # Daerah vs Tipe Channel
    st.subheader("Distribusi Tipe Channel per Daerah")

    region_channel = pd.crosstab(df_filtered['daerah'], df_filtered['tipeChannel'])

    fig_region_channel = px.imshow(
        region_channel,
        title="Heatmap: Daerah vs Tipe Channel",
        color_continuous_scale='Viridis',
        labels=dict(x="Tipe Channel", y="Daerah", color="Jumlah")
    )
    st.plotly_chart(fig_region_channel, use_container_width=True)

    # Detail per daerah
    st.subheader("Detail per Daerah")

    for daerah in df_filtered['daerah'].unique():
        with st.expander(f"📍 {daerah}"):
            df_daerah = df_filtered[df_filtered['daerah'] == daerah]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(df_daerah))
            col2.metric("Channel Terbanyak", df_daerah['tipeChannel'].value_counts().index[0])
            col3.metric("% Active", f"{(df_daerah['status']=='Active').mean()*100:.1f}%")

            st.write(df_daerah[['nama', 'tipeChannel', 'status', 'createdAt']].head(10))

with tab3:
    st.subheader("Analisis Tipe Channel")

    col1, col2 = st.columns(2)

    with col1:
        # Distribution chart
        fig_channel = px.pie(
            df_filtered,
            names='tipeChannel',
            title='Distribusi Tipe Channel',
            hole=0.4
        )
        fig_channel.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_channel, use_container_width=True)

    with col2:
        # Bar chart
        channel_counts = df_filtered['tipeChannel'].value_counts().reset_index()
        channel_counts.columns = ['Tipe Channel', 'Jumlah']

        fig_channel_bar = px.bar(
            channel_counts,
            x='Tipe Channel',
            y='Jumlah',
            title='Jumlah Customer per Tipe Channel',
            color='Jumlah',
            color_continuous_scale='Plasma'
        )
        st.plotly_chart(fig_channel_bar, use_container_width=True)

        # ==============================
    # 📊 STATUS PER TIPE CHANNEL
    # ==============================
    st.subheader("📊 Status per Tipe Channel")

    # Crosstab
    channel_status = pd.crosstab(
        df_filtered['tipeChannel'],
        df_filtered['status']
    ).reset_index()

    # ==============================
    # 🔹 ROW 1: CHART + SUMMARY
    # ==============================
    col1, col2 = st.columns([2, 1])

    with col1:
        fig_channel_status_bar = px.bar(
            channel_status,
            x='tipeChannel',
            y=channel_status.columns[1:],
            barmode='stack',
            title="Distribusi Active vs Inactive per Tipe Channel",
            labels=dict(value="Jumlah", tipeChannel="Tipe Channel", variable="Status")
        )
        st.plotly_chart(fig_channel_status_bar, use_container_width=True)

    with col2:
        st.markdown("### 📋 Ringkasan")
        st.dataframe(channel_status, use_container_width=True)

    # ==============================
    # 🔹 ROW 2: PERSENTASE
    # ==============================
    channel_status_pct = pd.crosstab(
        df_filtered['tipeChannel'],
        df_filtered['status'],
        normalize='index'
    ) * 100

    # ==============================
    # 🔹 ROW 3: ACTIVE vs INACTIVE
    # ==============================
    st.markdown("### 🔍 Detail Channel")

    colA, colB = st.columns(2)

    # ACTIVE
    with colA:
        st.markdown("#### ✅ Channel Active")

        if 'Active' in channel_status.columns:
            df_active = channel_status[['tipeChannel', 'Active']].copy()
            df_active = df_active[df_active['Active'] > 0]

            st.dataframe(
                df_active.sort_values('Active', ascending=False),
                use_container_width=True
            )
        else:
            st.info("Tidak ada data Active")

    # INACTIVE
    with colB:
        st.markdown("#### ❌ Channel Inactive")

        if 'Inactive' in channel_status.columns:
            df_inactive = channel_status[['tipeChannel', 'Inactive']].copy()
            df_inactive = df_inactive[df_inactive['Inactive'] > 0]

            st.dataframe(
                df_inactive.sort_values('Inactive', ascending=False),
                use_container_width=True
            )
        else:
            st.info("Tidak ada data Inactive")


    # Channel vs Status
    st.subheader("Status per Tipe Channel")

    channel_status = pd.crosstab(df_filtered['tipeChannel'], df_filtered['status'])

    fig_channel_status = px.imshow(
        channel_status,
        title="Heatmap: Tipe Channel vs Status",
        color_continuous_scale='RdYlGn',
        labels=dict(x="Status", y="Tipe Channel", color="Jumlah")
    )
    st.plotly_chart(fig_channel_status, use_container_width=True)

    # Channel vs Type
    st.subheader("Hubungan Tipe Channel dan Type (B2B/B2C)")

    # channel_type = pd.crosstab(df_filtered['tipeChannel'], df_filtered['type'])
    channel_type = pd.crosstab(df_filtered['tipeChannel'], df_filtered['type']).reset_index()

    channel_type_melt = channel_type.melt(
        id_vars='tipeChannel',
        var_name='Type',
        value_name='Jumlah'
    )

    fig_channel_type = px.bar(
        channel_type_melt,
        x='tipeChannel',
        y='Jumlah',
        color='Type',
        title="Distribusi B2B/B2C per Tipe Channel",
        barmode='stack'
    )
    # fig_channel_type = px.bar(
    #     channel_type.reset_index(),
    #     x='tipeChannel',
    #     y=['B2B', 'B2C'],
    #     title="Distribusi B2B/B2C per Tipe Channel",
    #     barmode='stack',
    #     labels=dict(value="Jumlah", tipeChannel="Tipe Channel", variable="Type", color="Type")
    # )
    st.plotly_chart(fig_channel_type, use_container_width=True)

with tab4:
    st.subheader("Analisis Kontrak dan Status")

    col1, col2 = st.columns(2)

    with col1:
        # Status distribution
        status_counts = df_filtered['status'].value_counts()

        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Distribusi Status Customer',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col2:
        # Type distribution
        type_counts = df_filtered['type'].value_counts()

        fig_type = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title='Distribusi Type (B2B/B2C)',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_type, use_container_width=True)

    # Contract duration distribution
    st.subheader("📅 Mayoritas Customer Ambil Kontrak Berapa Lama?")

    # Function kategori
    def categorize_duration(days):
        if days < 180:
            return "< 6 Bulan"
        elif days < 365:
            return "6–12 Bulan"
        elif days < 730:
            return "1–2 Tahun"
        else:
            return "> 2 Tahun"

    # Copy biar aman (hindari warning)
    df_filtered = df_filtered.copy()

    # Apply kategori
    df_filtered['kategoriDurasi'] = df_filtered['durasiKontrak'].apply(categorize_duration)

    # Hitung distribusi
    duration_counts = df_filtered['kategoriDurasi'].value_counts().reset_index()
    duration_counts.columns = ['Durasi', 'Jumlah']

    # Urutan kategori biar rapi
    order = ["< 6 Bulan", "6–12 Bulan", "1–2 Tahun", "> 2 Tahun"]
    duration_counts['Durasi'] = pd.Categorical(duration_counts['Durasi'], categories=order, ordered=True)
    duration_counts = duration_counts.sort_values('Durasi')

    # Tambah persentase
    duration_counts['Persentase (%)'] = (
        duration_counts['Jumlah'] / duration_counts['Jumlah'].sum() * 100
    ).round(1)

    # Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        fig_duration = px.bar(
            duration_counts,
            x='Durasi',
            y='Jumlah',
            text='Jumlah',
            title='Distribusi Durasi Kontrak'
        )
        fig_duration.update_traces(textposition='outside')
        st.plotly_chart(fig_duration, use_container_width=True)

    with col2:
        st.markdown("### 📋 Detail")
        st.dataframe(duration_counts, use_container_width=True)

    # Detail interaktif
    st.markdown("### 🔍 Detail Customer")

    selected_durasi = st.selectbox(
        "Pilih kategori durasi:",
        options=duration_counts['Durasi'].tolist()
    )

    df_detail_durasi = df_filtered[df_filtered['kategoriDurasi'] == selected_durasi]

    st.dataframe(
        df_detail_durasi[['nama', 'tipeChannel', 'durasiKontrak', 'status']],
        use_container_width=True
    )
    # df_filtered['kategoriDurasi'] = df_filtered['durasiKontrak'].apply(categorize_duration)

    # fig_duration = px.histogram(
    #     df_filtered,
    #     x='durasiKontrak',
    #     nbins=30,
    #     title='Distribusi Durasi Kontrak (Hari)',
    #     color='status',
    #     marginal='box'
    # )
    # st.plotly_chart(fig_duration, use_container_width=True)
    # Contract timeline
    # st.subheader("Timeline Kontrak")

    # df_timeline = df_filtered.copy()
    # df_timeline = df_timeline.sort_values('awalKontrak').tail(50)  # Last 50 for clarity

    # fig_timeline = go.Figure()

    # for idx, row in df_timeline.iterrows():
    #     fig_timeline.add_trace(go.Scatter(
    #         x=[row['awalKontrak'], row['akhirKontrak']],
    #         y=[row['nama'], row['nama']],
    #         mode='lines+markers',
    #         name=row['nama'],
    #         line=dict(color='green' if row['status'] == 'Active' else 'red', width=2),
    #         showlegend=False,
    #         hovertemplate=f"<b>{row['nama']}</b><br>" +
    #                      f"Channel: {row['tipeChannel']}<br>" +
    #                      f"Status: {row['status']}<br>" +
    #                      f"Durasi: {row['durasiKontrak']} hari<extra></extra>"
    #     ))

    # fig_timeline.update_layout(
    #     title="Timeline Kontrak Customer (50 Terakhir)",
    #     xaxis_title="Tanggal",
    #     yaxis_title="Customer",
    #     height=max(400, len(df_timeline) * 20),
    #     showlegend=False
    # )

    # st.plotly_chart(fig_timeline, use_container_width=True)

    # Status vs Daerah
    
    st.subheader("📍 Status Customer per Daerah")

    # Crosstab
    status_region = pd.crosstab(df_filtered['daerah'], df_filtered['status']).reset_index()

    # Persentase
    status_region_pct = pd.crosstab(
        df_filtered['daerah'],
        df_filtered['status'],
        normalize='index'
    ) * 100

    # Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        fig_status_region = px.bar(
            status_region,
            x='daerah',
            y=status_region.columns[1:],  # skip kolom 'daerah'
            barmode='stack',
            title="Distribusi Status per Daerah",
            labels=dict(value="Jumlah", daerah="Daerah", variable="Status")
        )
        st.plotly_chart(fig_status_region, use_container_width=True)

    with col2:
        st.markdown("### 📋 Jumlah")
        st.dataframe(status_region, use_container_width=True)

   
    with tab5:
        # Key Insights
        st.subheader("🔑 Key Insights - Pola Pengambilan Data Admin")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📍 Pola Wilayah")
            region_pattern = df_filtered['daerah'].value_counts()
            top_region = region_pattern.index[0]
            top_region_pct = (region_pattern.values[0] / len(df_filtered)) * 100

            st.metric(
                "Wilayah Terfokus",
                top_region,
                f"{top_region_pct:.1f}% dari total"
            )

            st.write(f"**Admin cenderung mengambil data dari wilayah {top_region}**")
            st.write(f"Rekomendasi: {'Perlu perluasan ke wilayah lain' if top_region_pct > 50 else 'Distribusi sudah merata'}")

            # Region by type
            st.markdown("#### Wilayah vs Type")
            region_type = pd.crosstab(df_filtered['daerah'], df_filtered['type'], normalize='index') * 100
            st.write(region_type.round(1).astype(str) + '%')

        with col2:
            st.markdown("### 🏪 Pola Tipe Channel")
            channel_pattern = df_filtered['tipeChannel'].value_counts()
            top_channel = channel_pattern.index[0]
            top_channel_pct = (channel_pattern.values[0] / len(df_filtered)) * 100

            st.metric(
                "Channel Terfokus",
                top_channel,
                f"{top_channel_pct:.1f}% dari total"
            )

            st.write(f"**Admin cenderung mengambil tipe channel {top_channel}**")
            st.write(f"Rekomendasi: {'Perlu diversifikasi channel' if top_channel_pct > 50 else 'Diversifikasi channel sudah baik'}")

            # Channel success rate
            st.markdown("#### Success Rate per Channel")
            channel_success = df_filtered.groupby('tipeChannel')['status'].apply(
                lambda x: (x == 'Active').mean() * 100
            ).sort_values(ascending=False)
            st.write(channel_success.round(1).astype(str) + '%')

        # Pattern Analysis
        st.subheader("📊 Analisis Pola Kontrak")

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_duration = df_filtered['durasiKontrak'].mean()
            st.metric("Rata-rata Durasi", f"{avg_duration:.0f} hari")

        with col2:
            active_rate = (df_filtered['status'] == 'Active').mean() * 100
            st.metric("Tingkat Aktivasi", f"{active_rate:.1f}%")

        with col3:
            b2b_ratio = (df_filtered['type'] == 'B2B').mean() * 100
            st.metric("Rasio B2B", f"{b2b_ratio:.1f}%")

        # Recommendation
        st.subheader("💼 Rekomendasi untuk Tim Sales")

        recommendations = []

        # Analyze region focus
        if top_region_pct > 60:
            recommendations.append(f"🎯 **Fokus Wilayah**: Admin sangat fokus pada {top_region} ({top_region_pct:.0f}%). " +
                                f"Pertimbangkan untuk ekspansi ke wilayah lain seperti {region_pattern.index[1]} atau {region_pattern.index[2]}")

        # Analyze channel focus
        if top_channel_pct > 60:
            recommendations.append(f"🏪 **Diversifikasi Channel**: {top_channel_pct:.0f}% data adalah {top_channel}. " +
                                f"Pertimbangkan channel lain dengan tingkat aktivasi tinggi")

        # Analyze contract patterns
        if avg_duration > 700:
            recommendations.append(f"📅 **Durasi Kontrak**: Rata-rata {avg_duration:.0f} hari ({avg_duration/365:.1f} tahun). " +
                                f"Kontrak jangka panjang menunjukkan kepercayaan customer yang baik")
        elif avg_duration < 400:
            recommendations.append(f"📅 **Durasi Kontrak**: Rata-rata {avg_duration:.0f} hari. " +
                                f"Pertimbangkan untuk menawarkan paket jangka panjang")

        # Analyze success rate
        if active_rate > 80:
            recommendations.append(f"✅ **Tingkat Aktivasi**: {active_rate:.1f}% sangat baik! " +
                                f"Admin memiliki kualitas seleksi yang tinggi")
        elif active_rate < 60:
            recommendations.append(f"⚠️ **Tingkat Aktivasi**: {active_rate:.1f}% perlu ditingkatkan. " +
                                f"Review kriteria seleksi admin")

        for rec in recommendations:
            st.success(rec)

        # Time trend
        st.subheader("📈 Tren Pendaftaran Customer Baru")

        df_filtered['date_only'] = df_filtered['createdAt'].dt.date
        daily_counts = df_filtered.groupby('date_only').size().reset_index(name='count')

        fig_trend = px.line(
            daily_counts,
            x='date_only',
            y='count',
            title='Tren Pendaftaran Customer Baru per Hari',
            markers=True
        )
        fig_trend.update_layout(
            xaxis_title="Tanggal",
            yaxis_title="Jumlah Customer Baru"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Final summary
        st.subheader("📝 Kesimpulan Eksekutif")

        summary_col1, summary_col2, summary_col3 = st.columns(3)

        with summary_col1:
            st.markdown("""
            <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; color: #333;">
                <h3>🎯 Fokus Utama</h3>
                <p><b>Wilayah:</b> {}</p>
                <p><b>Channel:</b> {}</p>
                <p><b>Type:</b> {}</p>
            </div>
            """.format(
                top_region,
                top_channel,
                df_filtered['type'].value_counts().index[0]
            ), unsafe_allow_html=True)

        with summary_col2:
            st.markdown("""
            <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; color: #333;">
                <h3>📊 Performa</h3>
                <p><b>Tingkat Aktivasi:</b> {:.1f}%</p>
                <p><b>Total Data:</b> {:,}</p>
                <p><b>Rata-rata Durasi:</b> {:.0f} hari</p>
            </div>
            """.format(
                active_rate,
                len(df_filtered),
                avg_duration
            ), unsafe_allow_html=True)

        with summary_col3:
            st.markdown("""
            <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; color: #333;">
                <h3>💡 Rekomendasi Utama</h3>
                <p>{}: {:.0f}% kontribusi</p>
                <p>Pertimbangkan diversifikasi ke segmen lain</p>
            </div>
            """.format(
                top_region,
                top_region_pct
            ), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📊 Customer Intelligence Dashboard | Data Analysis for Sales Team</p>
        <p>Generated on: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)
