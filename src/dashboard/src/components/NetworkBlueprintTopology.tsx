import React, { useState, useEffect } from 'react';
import { NetworkNode, NetworkLink, NodeStatus, FaultId } from '../types/network';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Info,
  Layers,
  Radio,
  Zap,
  PhoneCall,
  Globe,
  Lock,
  Server
} from 'lucide-react';

interface NetworkBlueprintTopologyProps {
  nodes: NetworkNode[];
  links: NetworkLink[];
  onSelectNode: (node: NetworkNode) => void;
  selectedNodeId?: string;
  activeFaultId?: FaultId;
}

export const NetworkBlueprintTopology: React.FC<NetworkBlueprintTopologyProps> = ({
  nodes,
  links,
  onSelectNode,
  selectedNodeId,
  activeFaultId,
}) => {
  const [zoom, setZoom] = useState<number>(0.95);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 10, y: 10 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [animationTick, setAnimationTick] = useState<number>(0);

  // Animation ticker for packet particles
  useEffect(() => {
    const timer = setInterval(() => {
      setAnimationTick((prev) => (prev + 1) % 100);
    }, 40);
    return () => clearInterval(timer);
  }, []);

  const handleResetView = () => {
    setZoom(0.95);
    setPan({ x: 10, y: 10 });
  };

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.15, 2.2));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.15, 0.5));

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  // ══════════════════════════════════════════════════════════════════════════════════
  // KIẾN TRÚC MẠNG DOANH NGHIỆP 3 CỘT CHUẨN MỰC (CỰC KỲ GỌN GÀNG, KHÔNG RỐI DÂY)
  // Cột Trái (x: 40 -> 580): 3 Chi Nhánh (Bảo Lộc, Nha Trang, TP.HCM)
  // Cột Giữa (x: 630 -> 1170): Đám mây SD-WAN 5 Kênh WAN Backbone
  // Cột Phải (x: 1210 -> 1770): Data Center (Spine-Leaf & Server Farm)
  // Luồng dữ liệu: Trái sang Phải chuẩn 100%, CHỈ TỪ TẦNG CORE MỚI NỐI RA WAN!
  // ══════════════════════════════════════════════════════════════════════════════════
  const nodeCoords: Record<string, { x: number; y: number; label: string; role: string; zone: string }> = {
    // ── 1. CHI NHÁNH BẢO LỘC (Zone 1 - Top Left) ──
    'BL-USERS': { x: 100, y: 105, label: 'BL Users (VLAN 10)', role: 'host', zone: 'baoloc' },
    'BL-WIFI': { x: 100, y: 170, label: 'BL WiFi (VLAN 50)', role: 'host', zone: 'baoloc' },
    'BL-IOT': { x: 100, y: 235, label: 'BL IoT / CCTV (30/35)', role: 'host', zone: 'baoloc' },
    'BL-SW': { x: 280, y: 170, label: 'BL-SW (L2 OVS)', role: 'access', zone: 'baoloc' },
    'BL-GW': { x: 490, y: 170, label: 'BL-GW (Core Router)', role: 'gateway', zone: 'baoloc' },

    // ── 2. CHI NHÁNH NHA TRANG (Zone 2 - Mid Left) ──
    'NT-HOSTS': { x: 90, y: 455, label: 'NT Endpoints (26 Hosts)', role: 'host', zone: 'nhatrang' },
    'NT-ACC01': { x: 195, y: 395, label: 'ACC01 (Admin)', role: 'access', zone: 'nhatrang' },
    'NT-ACC02': { x: 195, y: 455, label: 'ACC02 (Sales)', role: 'access', zone: 'nhatrang' },
    'NT-ACC03': { x: 195, y: 515, label: 'ACC03 (Acc/HR)', role: 'access', zone: 'nhatrang' },
    'NT-DIST01': { x: 335, y: 415, label: 'NT-DIST01 (VRRP Master)', role: 'dist', zone: 'nhatrang' },
    'NT-DIST02': { x: 335, y: 495, label: 'NT-DIST02 (VRRP Backup)', role: 'dist', zone: 'nhatrang' },
    'NT-CORE': { x: 490, y: 455, label: 'NT-CORE (Root STP 4096)', role: 'core', zone: 'nhatrang' },

    // ── 3. CHI NHÁNH TP. HỒ CHÍ MINH (Zone 3 - Bottom Left) ──
    'HCM-HOSTS': { x: 90, y: 745, label: 'HCM Endpoints (35 Hosts)', role: 'host', zone: 'hcm' },
    'HCM-ACC01': { x: 195, y: 685, label: 'ACC01 (Admin)', role: 'access', zone: 'hcm' },
    'HCM-ACC02': { x: 195, y: 745, label: 'ACC02 (Sales/Mkt)', role: 'access', zone: 'hcm' },
    'HCM-ACC03': { x: 195, y: 805, label: 'ACC03 (Tech/Voice)', role: 'access', zone: 'hcm' },
    'HCM-DIST01': { x: 335, y: 705, label: 'HCM-DIST01 (VRRP Master)', role: 'dist', zone: 'hcm' },
    'HCM-DIST02': { x: 335, y: 785, label: 'HCM-DIST02 (VRRP Backup)', role: 'dist', zone: 'hcm' },
    'HCM-CORE': { x: 490, y: 745, label: 'HCM-CORE (Root STP 4096)', role: 'core', zone: 'hcm' },

    // ── 4. DATA CENTER (Zone 4 - Right Column) ──
    'DC-SP-GW': { x: 1260, y: 455, label: 'DC-SP-GW (WAN Gateway)', role: 'gateway', zone: 'datacenter' },
    'DC-SPINE01': { x: 1400, y: 350, label: 'DC-SPINE01 (Root 4096)', role: 'spine', zone: 'datacenter' },
    'DC-SPINE02': { x: 1400, y: 560, label: 'DC-SPINE02 (Backup 8192)', role: 'spine', zone: 'datacenter' },
    'DC-LEAF01': { x: 1540, y: 230, label: 'LEAF01 (Web Tier)', role: 'leaf', zone: 'datacenter' },
    'DC-LEAF02': { x: 1540, y: 380, label: 'LEAF02 (App/SIP Tier)', role: 'leaf', zone: 'datacenter' },
    'DC-LEAF03': { x: 1540, y: 530, label: 'LEAF03 (DB Tier)', role: 'leaf', zone: 'datacenter' },
    'DC-LEAF04': { x: 1540, y: 680, label: 'LEAF04 (Infra Tier)', role: 'leaf', zone: 'datacenter' },
    'DC-SRV-WEB': { x: 1690, y: 230, label: 'WEB VIP (HAProxy 10.100.10.10)', role: 'server', zone: 'datacenter' },
    'DC-SRV-APP': { x: 1690, y: 380, label: 'APP01 (Asterisk SIP VoIP)', role: 'server', zone: 'datacenter' },
    'DC-SRV-DB': { x: 1690, y: 530, label: 'DB01/02 (MySQL Cluster)', role: 'server', zone: 'datacenter' },
    'DC-SRV-INFRA': { x: 1690, y: 680, label: 'Prometheus (:9090) / DNS', role: 'server', zone: 'datacenter' },
  };

  const getNodeState = (id: string): NodeStatus => {
    if (id === 'NT-ACC02') {
      const match = nodes.find((n) => n.id === 'NT-ACC02');
      return match ? match.status : 'ONLINE';
    }
    if (id === 'NT-DIST01') {
      const match = nodes.find((n) => n.id === 'NT-DIST01');
      return match ? match.status : 'ONLINE';
    }
    if (id === 'HCM-DIST01') {
      const match = nodes.find((n) => n.id === 'HCM-DIST01');
      return match ? match.status : 'ONLINE';
    }
    if (id === 'DC-SRV-WEB') {
      const match = nodes.find((n) => n.id === 'DC-SERVERS');
      return match ? match.status : 'ONLINE';
    }
    const match = nodes.find((n) => n.id === id);
    return match ? match.status : 'ONLINE';
  };

  const mplsLink = links.find((l) => l.transport === 'MPLS');
  const fiveGLink = links.find((l) => l.transport === '5G');
  const inetLink = links.find((l) => l.transport === 'Internet');
  const lteLink = links.find((l) => l.transport === 'LTE');
  const vpnLink = links.find((l) => l.transport === 'VPN');

  const isLinkFault = (source: string, target: string): boolean => {
    if (source === 'NT-DIST01' && target === 'NT-ACC02') {
      return getNodeState('NT-ACC02') === 'OFFLINE';
    }
    if (source === 'NT-CORE' && target === 'NT-DIST01') {
      return getNodeState('NT-DIST01') === 'OFFLINE';
    }
    if (source === 'BL-GW' && target === 'HCM-CORE') {
      return activeFaultId === 'F03';
    }
    return false;
  };

  return (
    <div className="flex flex-col bg-[#070b14] border border-slate-800 rounded-xl overflow-hidden shadow-2xl relative">
      {/* Blueprint Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-5 py-3 bg-slate-900/90 border-b border-slate-800 z-10 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          <h2 className="text-sm font-bold text-white uppercase font-mono tracking-wider">
            BẢN VẼ SƠ ĐỒ KIẾN TRÚC MẠNG TOÀN DOANH NGHIỆP (ENTERPRISE ARCHITECTURE BLUEPRINT)
          </h2>
          <span className="text-xs text-slate-400 font-mono hidden md:inline">
            · 3 Khối Chi Nhánh (Trái) ➔ Đám Mây SD-WAN 5 Kênh WAN (Giữa) ➔ Data Center Fabric (Phải)
          </span>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:text-cyan-300 text-slate-400 transition-colors"
            title="Phóng to"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <span className="text-xs text-slate-300 px-2 font-mono font-bold">{Math.round(zoom * 100)}%</span>
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:text-cyan-300 text-slate-400 transition-colors"
            title="Thu nhỏ"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetView}
            className="p-1.5 hover:text-cyan-300 text-slate-400 transition-colors"
            title="Khôi phục góc nhìn"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* SVG Canvas Workspace - ViewBox 1820 x 920 */}
      <div
        className="w-full h-[850px] bg-[#070b14] relative overflow-hidden select-none cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        {/* Grid Background Pattern */}
        <div 
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            backgroundImage: `radial-gradient(circle, #38bdf8 1.2px, transparent 1.2px)`,
            backgroundSize: `${28 * zoom}px ${28 * zoom}px`,
            backgroundPosition: `${pan.x}px ${pan.y}px`,
          }}
        />

        {/* Legend Overlay at Bottom-Left */}
        <div className="absolute bottom-4 left-4 z-10 p-3 rounded-lg bg-slate-950/90 border border-slate-800 text-xs font-mono backdrop-blur pointer-events-none shadow-xl">
          <div className="font-bold text-slate-200 uppercase mb-2 flex items-center gap-2">
            <Info className="w-4 h-4 text-cyan-400" /> Quy Chuẩn Thiết Kế Mạng Phân Tầng
          </div>
          <div className="grid grid-cols-2 gap-x-5 gap-y-1.5 text-slate-400 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              <span>Node / Link ONLINE</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,1)] animate-ping" />
              <span>SỰ CỐ / ĐỨT LINK</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-1 bg-emerald-400 inline-block rounded" />
              <span>MPLS (100M, 20ms)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-1 bg-cyan-400 inline-block rounded" />
              <span>5G (200M, 15ms)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-1 bg-amber-400 inline-block rounded" />
              <span>Internet (100M, 40ms)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-1 bg-purple-400 inline-block rounded" />
              <span>VPN (50M, 50ms)</span>
            </div>
            <div className="col-span-2 pt-1.5 border-t border-slate-800 text-[10.5px] text-cyan-300 font-semibold flex items-center gap-1.5">
              <span className="text-emerald-400 font-bold">★ Chuẩn Phân Tầng:</span>
              <span>Chỉ từ CORE mỗi chi nhánh (BL-GW, NT-CORE, HCM-CORE) mới nối WAN đổ về Data Center</span>
            </div>
          </div>
        </div>

        {/* SVG Drawing Layer */}
        <svg
          className="w-full h-full transition-transform"
          viewBox="0 0 1820 920"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'top left',
          }}
        >
          <defs>
            <filter id="bp-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* High-Tech Cyber HUD Selected Neon Glow Filter */}
            <filter id="selected-neon-glow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="4" result="blur1" />
              <feGaussianBlur stdDeviation="9" result="blur2" />
              <feMerge>
                <feMergeNode in="blur2" />
                <feMergeNode in="blur1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Radial Pulsing Aura for Selected Node */}
            <radialGradient id="selected-aura" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.5" />
              <stop offset="55%" stopColor="#06b6d4" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0891b2" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* ════════════════════════════════════════════════════════════════════════════════
              1. CỘT TRÁI: 3 PHÂN VÙNG CHI NHÁNH (RÕ RÀNG, NGĂN NẮP, KHÔNG ĐÈ LÊN NHAU)
          ════════════════════════════════════════════════════════════════════════════════ */}
          {/* Zone 1: BẢO LỘC (Top Left) */}
          <g>
            <rect x="35" y="45" width="530" height="255" rx="14" fill="#0f172a" fillOpacity="0.4" stroke="#334155" strokeWidth="1.5" />
            <text x="50" y="72" fill="#38bdf8" fontSize="12" fontWeight="bold" fontFamily="monospace">1. CHI NHÁNH BẢO LỘC (FLAT LAN)</text>
            <text x="50" y="88" fill="#64748b" fontSize="9.5" fontFamily="monospace">Subnet: 10.10.0.0/16 · 17 Hosts · Gateway kiêm Core Router</text>
          </g>

          {/* Zone 2: NHA TRANG (Mid Left) */}
          <g>
            <rect x="35" y="325" width="530" height="265" rx="14" fill="#0f172a" fillOpacity="0.4" stroke="#334155" strokeWidth="1.5" />
            <text x="50" y="352" fill="#38bdf8" fontSize="12" fontWeight="bold" fontFamily="monospace">2. CHI NHÁNH NHA TRANG (3-TIER LAN)</text>
            <text x="50" y="368" fill="#64748b" fontSize="9.5" fontFamily="monospace">Subnet: 10.20.0.0/16 · Access ➔ 2 Dist VRRP ➔ Core Switch (Root 4096)</text>
          </g>

          {/* Zone 3: TP. HỒ CHÍ MINH (Bottom Left) */}
          <g>
            <rect x="35" y="615" width="530" height="265" rx="14" fill="#0f172a" fillOpacity="0.4" stroke="#334155" strokeWidth="1.5" />
            <text x="50" y="642" fill="#38bdf8" fontSize="12" fontWeight="bold" fontFamily="monospace">3. CHI NHÁNH TP. HỒ CHÍ MINH (3-TIER LAN)</text>
            <text x="50" y="658" fill="#64748b" fontSize="9.5" fontFamily="monospace">Subnet: 10.30.0.0/16 · Access ➔ 2 Dist VRRP ➔ Core Switch (Root 4096)</text>
          </g>

          {/* ════════════════════════════════════════════════════════════════════════════════
              2. CỘT GIỮA: ĐÁM MÂY SD-WAN BACKBONE (5 KÊNH WAN ĐỘC LẬP)
          ════════════════════════════════════════════════════════════════════════════════ */}
          <g>
            <rect
              x="600"
              y="45"
              width="550"
              height="835"
              rx="16"
              fill="#081020"
              fillOpacity="0.85"
              stroke="#0284c7"
              strokeWidth="2"
              strokeDasharray="6 4"
            />
            <g transform="translate(875, 75)">
              <text x="0" y="0" fill="#38bdf8" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                SD-WAN MULTI-PATH BACKBONE CLOUD
              </text>
              <text x="0" y="16" fill="#10b981" fontSize="9.5" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                ★ 5 KÊNH WAN TIẾP NHẬN TỪ 3 CORE CHI NHÁNH ➔ ĐỔ VỀ DATA CENTER
              </text>
              <text x="0" y="28" fill="#64748b" fontSize="8.5" fontFamily="monospace" textAnchor="middle">
                Dynamic SLA Steering · AI PPO Closed-Loop Controller
              </text>
            </g>
          </g>

          {/* ════════════════════════════════════════════════════════════════════════════════
              3. CỘT PHẢI: DATA CENTER CENTRAL FABRIC (SPINE-LEAF & SERVER FARM)
          ════════════════════════════════════════════════════════════════════════════════ */}
          <g>
            <rect
              x="1190"
              y="45"
              width="595"
              height="835"
              rx="16"
              fill="#0f172a"
              fillOpacity="0.45"
              stroke="#a855f7"
              strokeWidth="2"
              strokeDasharray="6 4"
            />
            <g transform="translate(1485, 75)">
              <text x="0" y="0" fill="#c084fc" fontSize="13" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                DATA CENTER CENTRAL FABRIC (SPINE-LEAF)
              </text>
              <text x="0" y="16" fill="#e879f9" fontSize="9.5" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                Subnet: 10.100.0.0/16 · 10 Máy Chủ Cốt Lõi · HAProxy VIP 10.100.10.10
              </text>
              <text x="0" y="28" fill="#64748b" fontSize="8.5" fontFamily="monospace" textAnchor="middle">
                Cổng DC-SP-GW Tiếp Nhận Mọi Lưu Lượng Từ 3 Chi Nhánh
              </text>
            </g>
          </g>

          {/* ════════ LIÊN KẾT NỘI BỘ CHI NHÁNH (THẲNG HÀNG, KHÔNG RỐI) ════════ */}
          {/* Bảo Lộc LAN */}
          {renderWireLink('BL-USERS', 'BL-SW')}
          {renderWireLink('BL-WIFI', 'BL-SW')}
          {renderWireLink('BL-IOT', 'BL-SW')}
          {renderWireLink('BL-SW', 'BL-GW')}

          {/* Nha Trang LAN: Hosts -> Access -> Dist -> Core */}
          {renderWireLink('NT-HOSTS', 'NT-ACC01')}
          {renderWireLink('NT-HOSTS', 'NT-ACC02')}
          {renderWireLink('NT-HOSTS', 'NT-ACC03')}
          {renderWireLink('NT-ACC01', 'NT-DIST01')}
          {renderWireLink('NT-ACC02', 'NT-DIST01')}
          {renderWireLink('NT-ACC03', 'NT-DIST02')}
          {renderWireLink('NT-ACC02', 'NT-DIST02')}
          {renderHeartbeatLink('NT-DIST01', 'NT-DIST02', 'VRRP')}
          {renderWireLink('NT-DIST01', 'NT-CORE')}
          {renderWireLink('NT-DIST02', 'NT-CORE')}

          {/* TP.HCM LAN: Hosts -> Access -> Dist -> Core */}
          {renderWireLink('HCM-HOSTS', 'HCM-ACC01')}
          {renderWireLink('HCM-HOSTS', 'HCM-ACC02')}
          {renderWireLink('HCM-HOSTS', 'HCM-ACC03')}
          {renderWireLink('HCM-ACC01', 'HCM-DIST01')}
          {renderWireLink('HCM-ACC02', 'HCM-DIST01')}
          {renderWireLink('HCM-ACC03', 'HCM-DIST02')}
          {renderWireLink('HCM-ACC02', 'HCM-DIST02')}
          {renderHeartbeatLink('HCM-DIST01', 'HCM-DIST02', 'VRRP')}
          {renderWireLink('HCM-DIST01', 'HCM-CORE')}
          {renderWireLink('HCM-DIST02', 'HCM-CORE')}

          {/* Data Center Internal: DC-SP-GW -> Spines -> Leafs -> Servers */}
          {renderWireLink('DC-SP-GW', 'DC-SPINE01')}
          {renderWireLink('DC-SP-GW', 'DC-SPINE02')}
          {renderHeartbeatLink('DC-SPINE01', 'DC-SPINE02', 'ISL Trunk')}
          {renderWireLink('DC-SPINE01', 'DC-LEAF01')}
          {renderWireLink('DC-SPINE01', 'DC-LEAF02')}
          {renderWireLink('DC-SPINE01', 'DC-LEAF03')}
          {renderWireLink('DC-SPINE01', 'DC-LEAF04')}
          {renderWireLink('DC-SPINE02', 'DC-LEAF01')}
          {renderWireLink('DC-SPINE02', 'DC-LEAF02')}
          {renderWireLink('DC-SPINE02', 'DC-LEAF03')}
          {renderWireLink('DC-SPINE02', 'DC-LEAF04')}
          {renderWireLink('DC-LEAF01', 'DC-SRV-WEB')}
          {renderWireLink('DC-LEAF02', 'DC-SRV-APP')}
          {renderWireLink('DC-LEAF03', 'DC-SRV-DB')}
          {renderWireLink('DC-LEAF04', 'DC-SRV-INFRA')}

          {/* ════════ KẾT NỐI CHỈ TỪ CORE 3 CHI NHÁNH VÀO SD-WAN CLOUD ════════ */}
          {/* Core Uplink Bảo Lộc (BL-GW) vào Ingress WAN */}
          {renderCoreIngressLink(
            nodeCoords['BL-GW'],
            600,
            170,
            '#10b981',
            'BL-GW CORE UPLINK'
          )}

          {/* Core Uplink Nha Trang (NT-CORE) vào Ingress WAN */}
          {renderCoreIngressLink(
            nodeCoords['NT-CORE'],
            600,
            455,
            '#06b6d4',
            'NT-CORE UPLINK'
          )}

          {/* Core Uplink TP.HCM (HCM-CORE) vào Ingress WAN */}
          {renderCoreIngressLink(
            nodeCoords['HCM-CORE'],
            600,
            745,
            '#818cf8',
            'HCM-CORE UPLINK'
          )}

          {/* ════════ 5 ĐƯỜNG TRUYỀN WAN THẲNG TẮP TRONG CLOUD ➔ ĐỔ VÀO DC-SP-GW ════════ */}
          {/* 1. MPLS Dedicated (100M, 20ms) - Emerald */}
          {renderStraightWanChannel(
            600,
            1150,
            170,
            nodeCoords['DC-SP-GW'],
            'MPLS DEDICATED',
            '100 Mbps · 20 ms · Loss 0.1%',
            'VoIP SIP & ERP DB',
            '#10b981',
            mplsLink?.status === 'DOWN',
            mplsLink?.status === 'CONGESTED'
          )}

          {/* 2. 5G Ultra-Low Latency (200M, 15ms) - Cyan */}
          {renderStraightWanChannel(
            600,
            1150,
            310,
            nodeCoords['DC-SP-GW'],
            '5G ULTRA-LOW LATENCY',
            '200 Mbps · 15 ms · Loss 0.3%',
            'Video Conf & Real-time Telemetry',
            '#06b6d4',
            fiveGLink?.status === 'DOWN',
            fiveGLink?.lossPercent !== undefined && fiveGLink.lossPercent > 5
          )}

          {/* 3. Broadband Internet (100M, 40ms) - Amber */}
          {renderStraightWanChannel(
            600,
            1150,
            455,
            nodeCoords['DC-SP-GW'],
            'BROADBAND INTERNET',
            '100 Mbps · 40 ms · Loss 0.5%',
            'Web HTTP/S & Cloud SaaS',
            '#f59e0b',
            inetLink?.status === 'DOWN',
            false
          )}

          {/* 4. 4G/LTE Cellular Backup (30M, 60ms) - Indigo */}
          {renderStraightWanChannel(
            600,
            1150,
            600,
            nodeCoords['DC-SP-GW'],
            '4G/LTE CELLULAR',
            '30 Mbps · 60 ms · Loss 1.0%',
            'Cellular Standby Failover',
            '#6366f1',
            lteLink?.status === 'DOWN',
            false
          )}

          {/* 5. IPsec VPN Encrypted Tunnel (50M, 50ms) - Pink */}
          {renderStraightWanChannel(
            600,
            1150,
            745,
            nodeCoords['DC-SP-GW'],
            'IPSEC ENCRYPTED TUNNEL',
            '50 Mbps · 50 ms · Loss 0.8%',
            'Nightly Encrypted DB Backup',
            '#ec4899',
            vpnLink?.status === 'DOWN',
            false
          )}

          {/* ════════ BIỂU TƯỢNG HỘI TỤ DATA CENTER (HUB CONVERGENCE) ════════ */}
          <g transform={`translate(${nodeCoords['DC-SP-GW'].x}, ${nodeCoords['DC-SP-GW'].y - 48})`}>
            <rect
              x="-150"
              y="-13"
              width="300"
              height="26"
              rx="6"
              fill="#1e1b4b"
              stroke="#a855f7"
              strokeWidth={1.8}
            />
            <text x="0" y="4" fill="#f0abfc" fontSize="9" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              ★ HUB HỘI TỤ: 3 CORE CHI NHÁNH ĐỔ VỀ ĐÂY
            </text>
          </g>

          {/* ════════ VẼ TẤT CẢ CÁC NODE THIẾT BỊ RÕ RÀNG, BỐ TRÍ NGĂN NẮP ════════ */}
          {Object.entries(nodeCoords).map(([id, info]) => {
            const state = getNodeState(id);
            const isSelected = selectedNodeId === id;
            return renderNodeGlyph(id, info, state, isSelected);
          })}
        </svg>
      </div>
    </div>
  );

  // Wire links rendering
  function renderWireLink(sourceId: string, targetId: string) {
    const s = nodeCoords[sourceId];
    const t = nodeCoords[targetId];
    if (!s || !t) return null;

    const isFault = isLinkFault(sourceId, targetId);
    const isConnectedToSelected = selectedNodeId === sourceId || selectedNodeId === targetId;

    return (
      <g key={`link-${sourceId}-${targetId}`}>
        <line
          x1={s.x}
          y1={s.y}
          x2={t.x}
          y2={t.y}
          stroke={isFault ? '#f43f5e' : isConnectedToSelected ? '#22d3ee' : '#334155'}
          strokeWidth={isFault ? 3.5 : isConnectedToSelected ? 2.8 : 1.8}
          strokeDasharray={isFault ? '7 4' : 'none'}
          className={isFault ? 'animate-pulse' : ''}
          filter={isConnectedToSelected ? 'url(#bp-glow)' : undefined}
        />
        {!isFault && (
          <circle
            cx={s.x + (t.x - s.x) * ((animationTick % 100) / 100)}
            cy={s.y + (t.y - s.y) * ((animationTick % 100) / 100)}
            r={isConnectedToSelected ? 3.8 : 2.5}
            fill={isConnectedToSelected ? '#67e8f9' : '#38bdf8'}
            filter="url(#bp-glow)"
          />
        )}
      </g>
    );
  }

  // Heartbeat link
  function renderHeartbeatLink(sourceId: string, targetId: string, label: string) {
    const s = nodeCoords[sourceId];
    const t = nodeCoords[targetId];
    if (!s || !t) return null;

    const midX = (s.x + t.x) / 2;
    const midY = (s.y + t.y) / 2;

    return (
      <g key={`hb-${sourceId}-${targetId}`}>
        <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#4f46e5" strokeWidth={2.2} strokeDasharray="4 3" />
        <rect x={midX - 25} y={midY - 8} width={50} height={16} rx={3} fill="#0f172a" stroke="#4338ca" strokeWidth={1.2} />
        <text x={midX} y={midY + 3.5} fill="#a5b4fc" fontSize={8.5} fontWeight="bold" fontFamily="monospace" textAnchor="middle">
          {label}
        </text>
      </g>
    );
  }

  // Core Ingress Link from Branch Core node into SD-WAN Cloud entrance
  function renderCoreIngressLink(
    coreNode: { x: number; y: number },
    cloudEntranceX: number,
    entranceY: number,
    color: string,
    label: string
  ) {
    const pathD = `M ${coreNode.x} ${coreNode.y} L ${cloudEntranceX} ${entranceY}`;
    const pT = (animationTick % 100) / 100;
    const pX = coreNode.x + (cloudEntranceX - coreNode.x) * pT;
    const pY = coreNode.y + (entranceY - coreNode.y) * pT;

    return (
      <g key={`core-ingress-${label}`}>
        <path d={pathD} fill="none" stroke={color} strokeWidth={2.5} />
        <circle cx={pX} cy={pY} r={3.5} fill="#ffffff" filter="url(#bp-glow)" />
        {/* Small badge */}
        <g transform={`translate(${(coreNode.x + cloudEntranceX) / 2}, ${coreNode.y - 12})`}>
          <rect x="-65" y="-8" width="130" height="16" rx="3" fill="#090d16" stroke={color} strokeWidth={1.2} />
          <text x="0" y="3.5" fill={color} fontSize="8" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
            {label}
          </text>
        </g>
      </g>
    );
  }

  // ════════ VẼ 5 ĐƯỜNG TRUYỀN WAN THẲNG TẮP, THOÁNG ĐÃNG TRONG ĐÁM MÂY ════════
  function renderStraightWanChannel(
    cloudLeftX: number,
    cloudRightX: number,
    channelY: number,
    dcGateway: { x: number; y: number },
    name: string,
    specs: string,
    appClass: string,
    color: string,
    isDown: boolean,
    isDegraded: boolean
  ) {
    // Đoạn 1: Thẳng tắp xuyên qua đám mây từ trái qua phải (cloudLeftX -> cloudRightX)
    const straightPath = `M ${cloudLeftX} ${channelY} L ${cloudRightX} ${channelY}`;
    // Đoạn 2: Từ mép phải đám mây uốn lượn mượt mà hội tụ vào DC-SP-GW
    const toDcPath = `M ${cloudRightX} ${channelY} C ${cloudRightX + 45} ${channelY}, ${dcGateway.x - 45} ${dcGateway.y}, ${dcGateway.x} ${dcGateway.y}`;

    const midCloudX = (cloudLeftX + cloudRightX) / 2;
    const pT = (animationTick % 100) / 100;
    const particleX = cloudLeftX + (cloudRightX - cloudLeftX) * pT;

    return (
      <g key={`wan-channel-${name}`}>
        {/* Đường chạy ngang qua đám mây */}
        <path
          d={straightPath}
          fill="none"
          stroke={isDown ? '#f43f5e' : color}
          strokeWidth={isDown ? 3.5 : 2.8}
          strokeDasharray={isDown ? '8 4' : 'none'}
          className={isDown ? 'animate-pulse' : ''}
        />

        {/* Đường uốn vào cổng DC-SP-GW */}
        <path
          d={toDcPath}
          fill="none"
          stroke={isDown ? '#f43f5e' : color}
          strokeWidth={isDown ? 3 : 2.2}
          strokeDasharray={isDown ? '6 4' : 'none'}
          opacity={0.85}
        />

        {/* Gói tin chạy ngang mượt mà đổ về Data Center */}
        {!isDown && (
          <circle cx={particleX} cy={channelY} r={4} fill={isDegraded ? '#fbbf24' : '#ffffff'} filter="url(#bp-glow)" />
        )}

        {/* Capsule thông số thanh thoát ngay giữa đường truyền */}
        <g transform={`translate(${midCloudX}, ${channelY})`}>
          <rect
            x="-140"
            y="-18"
            width="280"
            height="36"
            rx="6"
            fill={isDown ? '#450a0a' : '#0a1324'}
            stroke={isDown ? '#f43f5e' : color}
            strokeWidth={isDown ? 2 : 1.4}
            className={isDown ? 'animate-pulse' : ''}
          />
          <circle cx="-123" cy="0" r="5" fill={isDown ? '#ef4444' : color} />
          <text x="-110" y="-3" fill={isDown ? '#fca5a5' : '#f8fafc'} fontSize="9.5" fontWeight="bold" fontFamily="monospace">
            {isDown ? `❌ ${name} (DOWN)` : name}
          </text>
          <text x="-110" y="10" fill={isDown ? '#fda4af' : '#94a3b8'} fontSize="8" fontFamily="monospace">
            {specs} · <tspan fill={color} fontWeight="bold">{appClass}</tspan>
          </text>
        </g>
      </g>
    );
  }

  // Node Glyphs
  function renderNodeGlyph(
    id: string,
    info: { x: number; y: number; label: string; role: string; zone: string },
    status: NodeStatus,
    isSelected: boolean
  ) {
    const isDown = status === 'OFFLINE';
    const isDegraded = status === 'DEGRADED';
    const isRecovering = status === 'RECOVERING';

    const nodeMatch = nodes.find((n) => n.id === id);

    let fillColor = '#0f172a';
    let strokeColor = '#38bdf8';
    if (isDown) {
      fillColor = '#450a0a';
      strokeColor = '#f43f5e';
    } else if (isDegraded) {
      fillColor = '#451a03';
      strokeColor = '#f59e0b';
    } else if (isRecovering) {
      fillColor = '#083344';
      strokeColor = '#22d3ee';
    } else if (info.role === 'server') {
      strokeColor = '#a855f7';
    } else if (info.role === 'dist' || info.role === 'gateway') {
      strokeColor = '#6366f1';
    } else if (info.role === 'core' || info.role === 'spine') {
      strokeColor = '#06b6d4';
    }

    const radius =
      info.role === 'core' || info.role === 'gateway' || info.role === 'spine'
        ? 20
        : info.role === 'dist'
        ? 18
        : 15;

    return (
      <g
        key={id}
        transform={`translate(${info.x}, ${info.y})`}
        className="cursor-pointer transition-transform hover:scale-110"
        onClick={() => {
          if (nodeMatch) onSelectNode(nodeMatch);
        }}
      >
        {isDown && (
          <circle cx="0" cy="0" r={radius + 10} fill="none" stroke="#f43f5e" strokeWidth={2} opacity="0.8" className="animate-ping" />
        )}

        {/* ══ HIỆU ỨNG SELECTION CYBER HUD NỔI BẬT CÔNG NGHỆ CAO ══ */}
        {isSelected && (
          <g>
            {/* 1. Hào quang Neon Aura phát sáng lan tỏa */}
            <circle
              cx="0"
              cy="0"
              r={radius + 26}
              fill="url(#selected-aura)"
              className="animate-pulse"
            />

            {/* 2. Sóng radar xung kích lan tỏa (Radar Wave Ripple) */}
            <circle
              cx="0"
              cy="0"
              r={radius + 16}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="1.8"
              opacity="0.85"
              className="animate-ping"
            />

            {/* 3. Vòng tròn HUD xoay công nghệ với vạch ngắm radar */}
            <circle
              cx="0"
              cy="0"
              r={radius + 11}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeDasharray="6 3 2 3"
              style={{
                transformOrigin: '0px 0px',
                animation: 'spin 12s linear infinite',
              }}
            />

            {/* 4. 4 Khung ngắm Radar HUD Target Brackets (┌ ┐ └ ┘) */}
            <path
              d={`M ${-radius - 8} ${-radius - 2} L ${-radius - 8} ${-radius - 8} L ${-radius - 2} ${-radius - 8}`}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#selected-neon-glow)"
            />
            <path
              d={`M ${radius + 2} ${-radius - 8} L ${radius + 8} ${-radius - 8} L ${radius + 8} ${-radius - 2}`}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#selected-neon-glow)"
            />
            <path
              d={`M ${-radius - 8} ${radius + 2} L ${-radius - 8} ${radius + 8} L ${-radius - 2} ${radius + 8}`}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#selected-neon-glow)"
            />
            <path
              d={`M ${radius + 2} ${radius + 8} L ${radius + 8} ${radius + 8} L ${radius + 8} ${radius + 2}`}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#selected-neon-glow)"
            />

            {/* 5. Tag HUD Cyber "TARGET ACTIVE" Trên Đỉnh */}
            <g transform={`translate(0, ${-radius - 22})`}>
              <rect
                x="-46"
                y="-9"
                width="92"
                height="18"
                rx="4"
                fill="#083344"
                stroke="#22d3ee"
                strokeWidth="1.5"
                filter="url(#selected-neon-glow)"
              />
              <circle cx="-34" cy="0" r="3" fill="#22d3ee" className="animate-ping" />
              <circle cx="-34" cy="0" r="2" fill="#ffffff" />
              <text
                x="6"
                y="3.5"
                fill="#a5f3fc"
                fontSize="8"
                fontWeight="bold"
                fontFamily="monospace"
                textAnchor="middle"
              >
                INSPECTING
              </text>
            </g>
          </g>
        )}

        {/* Node base body */}
        <circle
          cx="0"
          cy="0"
          r={radius}
          fill={isSelected ? '#083344' : fillColor}
          stroke={isSelected ? '#22d3ee' : strokeColor}
          strokeWidth={isSelected ? 3.2 : 2.2}
          filter={isSelected ? 'url(#selected-neon-glow)' : undefined}
        />

        {/* Center dot */}
        <circle
          cx="0"
          cy="0"
          r={isSelected ? 5 : 4}
          fill={isSelected ? '#67e8f9' : isDown ? '#f43f5e' : isDegraded ? '#fbbf24' : '#34d399'}
          className={isSelected ? 'animate-pulse' : ''}
        />

        {/* Node Label underneath */}
        <text
          x="0"
          y={radius + 13}
          fill={isSelected ? '#38bdf8' : isDown ? '#f43f5e' : '#f8fafc'}
          fontSize={isSelected ? '11' : '10'}
          fontWeight="bold"
          fontFamily="monospace"
          textAnchor="middle"
        >
          {id}
        </text>

        {/* Subtitle / IP */}
        <text x="0" y={radius + 24} fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">
          {nodeMatch?.ip ? nodeMatch.ip.split('/')[0] : info.label.slice(0, 16)}
        </text>

        {/* VRRP Master Tag Badge */}
        {nodeMatch?.vrrpRole && (
          <g transform={`translate(0, ${-radius - 10})`}>
            <rect
              x="-26"
              y="-7"
              width="52"
              height="15"
              rx="3"
              fill={nodeMatch.vrrpRole === 'MASTER' ? '#312e81' : '#1e293b'}
              stroke={nodeMatch.vrrpRole === 'MASTER' ? '#818cf8' : '#475569'}
              strokeWidth={1.2}
            />
            <text x="0" y="3.5" fill={nodeMatch.vrrpRole === 'MASTER' ? '#c7d2fe' : '#94a3b8'} fontSize="8" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
              VRRP {nodeMatch.vrrpRole}
            </text>
          </g>
        )}
      </g>
    );
  }
};
