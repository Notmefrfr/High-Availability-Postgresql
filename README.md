# PostgreSQL High Availability Cluster with Patroni & etcd

Proyek ini mengimplementasikan solusi **High Availability (HA)** untuk database PostgreSQL. Sistem ini dirancang untuk menghilangkan *single point of failure* dengan melakukan otomatisasi failover menggunakan mekanisme konsensus.

## 🚀 Fitur Utama
- **Automated Failover:** Perpindahan peran Leader otomatis saat terjadi kegagalan node melalui Patroni.
- **Distributed Configuration:** Menggunakan `etcd` sebagai sumber kebenaran (Source of Truth) untuk status klaster.
- **Load Balancing:** Pemisahan lalu lintas Read-Write (Port 5432) dan Read-Only (Port 5433) menggunakan HAProxy.
- **Health Monitoring:** Health check berbasis REST API (Port 8008).

## 🏗️ Arsitektur Sistem
Sistem terdiri dari 3 node utama:
1. **Node Master (192.168.56.101):** PostgreSQL + Patroni.
2. **Node Slave (192.168.56.102):** PostgreSQL + Patroni (Replica).
3. **Load Balancer (192.168.56.103):** HAProxy + etcd.



## 🛠️ Tech Stack
- **Database:** PostgreSQL 16
- **HA Manager:** Patroni
- **DCS:** etcd
- **Load Balancer:** HAProxy
- **OS:** Ubuntu 24.04 LTS

## 📋 Tahapan Implementasi (Phases)
Proyek ini diselesaikan dalam 5 fase utama:
1. **Phase 1:** Instalasi PostgreSQL & Streaming Replication manual.
2. **Phase 2:** Konfigurasi HAProxy untuk pemisahan trafik RW/RO.
3. **Phase 3:** Integrasi Aplikasi ke Load Balancer.
4. **Phase 4:** Implementasi otomatisasi dengan Patroni & etcd.
5. **Phase 5:** Pengujian skenario Failover dan verifikasi sinkronisasi LSN.

## 🔍 Cara Verifikasi Klaster
Untuk melihat status klaster secara real-time, jalankan perintah berikut di salah satu node:
```bash
patronictl -c /etc/patroni/patroni.yml list
