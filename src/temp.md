sudo mn -c; sudo pkill -9 python3; sudo pkill -9 mn; sudo ovs-vsctl list-br | xargs -r -n1 sudo ovs-vsctl del-br; sudo ip link del HCM_DIST01_w2 2>/dev/null || true; sudo ip link del NT_DIST01_w2 2>/dev/null || true

sudo mn -c
sudo pkill -9 -f frr
sudo pkill -9 -f keepalived
sudo pkill -9 python3


sudo python3 -m ai_engine.telemetry.collector --save-dataset


# HƯỚNG DẪN KHÔI PHỤC MININET CHO DỰ ÁN KLTN

## 1. Nguyên nhân lỗi

Dự án sử dụng Python 3.9 trong môi trường ảo `.venv`, nhưng Mininet trên máy lại nằm trong thư mục của Python 3.12.

Khi chạy:

```bash
sudo -E python3 topology/enterprise_topo.py
```

Python có thể không tìm thấy thư viện Mininet hoặc Flask vì `sudo` sử dụng Python và đường dẫn thư viện khác với môi trường ảo.

**Cách xử lý:** Giữ Python 3.9 để chạy các module KLTN, cài mã nguồn Mininet tương thích vào `.venv` và gọi trực tiếp Python của môi trường ảo.

## 2. Kiểm tra cấu trúc dự án

Cấu trúc thư mục:

```text
KLTN/
├── mininet-src/
└── src/
    ├── .venv/
    │   └── bin/python3
    └── topology/
        └── enterprise_topo.py
```

Các đường dẫn quan trọng:

- Thư mục dự án: `~/KLTN/KLTN`
- Mã nguồn Mininet: `~/KLTN/KLTN/mininet-src`
- Môi trường Python: `~/KLTN/KLTN/src/.venv`
- File topology: `~/KLTN/KLTN/src/topology/enterprise_topo.py`

## 3. Quy trình khôi phục trên máy mới

### Bước 1: Cài các công cụ và thành phần hệ thống

Trên Ubuntu, kiểm tra và cài các gói cần thiết:

```bash
sudo apt update
sudo apt install git openvswitch-switch iproute2 iperf
```

Máy cũng cần có các thành phần hệ thống Mininet cần thiết. Nếu Mininet chưa được cài đặt hoặc chưa hoạt động, cần thiết lập chúng trước khi chạy topology.

### Bước 2: Tạo môi trường Python 3.9

Nếu máy chưa có Python 3.9, cần cài đặt Python 3.9 trước.

Tại thư mục dự án:

```bash
cd ~/KLTN/KLTN/src
python3.9 -m venv .venv
source .venv/bin/activate
```

Kiểm tra:

```bash
python3 --version
which python3
```

Kết quả mong muốn:

```text
Python 3.9.x
/home/baobao/KLTN/KLTN/src/.venv/bin/python3
```

### Bước 3: Cài các thư viện Python của dự án

Cài các thư viện theo file `requirements.txt` của dự án nếu đã có:

```bash
python3 -m pip install -r requirements.txt
```

Nếu chưa có file này, cần cài lại các thư viện mà dự án thực sự sử dụng, chẳng hạn Flask và Flask-SocketIO.

```bash
python3 -m pip install Flask Flask-SocketIO
```

Không cài lại toàn bộ thư viện một cách tùy tiện nếu môi trường đã được khôi phục đầy đủ.

### Bước 4: Tải mã nguồn Mininet

Tại thư mục dự án:

```bash
cd ~/KLTN/KLTN
git clone https://github.com/mininet/mininet.git mininet-src
cd mininet-src
git checkout 2.3.0
```

Nếu `mininet-src` đã tồn tại, không cần clone lại.

### Bước 5: Cài Mininet vào Python 3.9

Chạy:

```bash
cd ~/KLTN/KLTN/mininet-src
~/KLTN/KLTN/src/.venv/bin/python3 -m pip install .
```

Lệnh này cài gói Python từ mã nguồn Mininet vào môi trường `.venv`, không thay đổi Python của dự án sang phiên bản 3.12.

Lưu ý: Việc cài gói Python không thay thế cho các thành phần mạng hệ thống mà Mininet yêu cầu.

### Bước 6: Kiểm tra Flask và Mininet

Kiểm tra Flask:

```bash
~/KLTN/KLTN/src/.venv/bin/python3 -c \
"import flask; print(flask.__file__)"
```

Kiểm tra Mininet:

```bash
~/KLTN/KLTN/src/.venv/bin/python3 -c \
"from mininet.net import Mininet; print('Mininet OK')"
```

Nếu cả hai lệnh chạy thành công, các module Python cần thiết đã được nhận diện.

### Bước 7: Chạy topology

```bash
cd ~/KLTN/KLTN/src
sudo -E /home/baobao/KLTN/KLTN/src/.venv/bin/python3 topology/enterprise_topo.py
```

Lệnh này gọi trực tiếp Python trong `.venv`, tránh việc vô tình sử dụng Python hệ thống.

## 4. Xử lý các lỗi thường gặp

### Lỗi `No module named 'mininet'`

Kiểm tra:

```bash
.venv/bin/python3 -c \
"from mininet.net import Mininet; print('Mininet OK')"
```

Nếu lỗi, kiểm tra lại việc cài Mininet bằng Python trong `.venv` ở Bước 5.

### Lỗi `Flask not installed`

Kiểm tra:

```bash
sudo -E .venv/bin/python3 -c \
"import flask; print(flask.__file__)"
```

Nếu không import được Flask, cài Flask vào `.venv`:

```bash
.venv/bin/python3 -m pip install Flask Flask-SocketIO
```

Nếu import Flask thành công nhưng chương trình vẫn cảnh báo, kiểm tra đoạn `try/except` xử lý import trong `enterprise_topo.py`.

### Lỗi `Address already in use`

Kiểm tra tiến trình chiếm cổng, ví dụ cổng 9302:

```bash
sudo lsof -i :9302
```

Chỉ dừng tiến trình khi đã xác định đúng dịch vụ cần dừng:

```bash
sudo kill <PID>
```

Thay `<PID>` bằng PID thực tế của tiến trình.

### Lỗi Mininet cần quyền root

Chạy topology với `sudo -E` và đường dẫn Python tuyệt đối trong `.venv`. Không dùng `sudo python3` nếu chưa xác nhận Python đó chính là Python của môi trường ảo.

## 5. Các lưu ý quan trọng

1. Không xóa `.venv` nếu chưa sao lưu danh sách thư viện.
2. Không thêm trực tiếp thư mục thư viện Python 3.12 vào Python 3.9.
3. Không sử dụng `sudo pip install` để cài thư viện vào môi trường ảo.
4. Giữ lại mã nguồn `mininet-src` và tag `2.3.0` để có thể cài lại khi cần.
5. Nên lưu danh sách thư viện dự án:

```bash
cd ~/KLTN/KLTN/src
source .venv/bin/activate
python -m pip freeze > requirements.txt
```

Trên máy mới, kiểm tra `requirements.txt` trước khi dùng để khôi phục. File này ghi lại các gói Python đang cài, nhưng không bao gồm các thành phần hệ thống như Open vSwitch.

## 6. Checklist sau khi khôi phục

- [ ] Python trong `.venv` là phiên bản 3.9.
- [ ] Flask import thành công.
- [ ] Mininet import thành công.
- [ ] Các thành phần mạng hệ thống đã sẵn sàng.
- [ ] `enterprise_topo.py` chạy bằng Python trong `.venv`.
- [ ] REST API hoạt động nếu được bật trong cấu hình topology.
----------------
---------------
# Chạy exporter quét mạng Mininet:
python3 controller/sdn/telemetry_exporter.py &

pkill -f telemetry_exporter.py

# Chạy Prometheus:
prometheus --config.file=config/prometheus.yml --storage.tsdb.path=data/prometheus_data &

