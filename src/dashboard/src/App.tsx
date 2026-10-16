/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  NetworkNode, 
  NetworkLink, 
  WANPathMetric, 
  FaultScenario, 
  PPOStateVector, 
  PPOActionOutput, 
  SafetyLayerAudit, 
  IncidentLog, 
  FaultId 
} from './types/network';
import { 
  INITIAL_NODES, 
  INITIAL_LINKS, 
  INITIAL_WAN_METRICS, 
  FAULT_SCENARIOS 
} from './data/networkTopologyData';
import { NocHeader } from './components/NocHeader';
import { NetworkBlueprintTopology } from './components/NetworkBlueprintTopology';
import { InteractiveScenarioStudio } from './components/InteractiveScenarioStudio';
import { WanMonitorPanel } from './components/WanMonitorPanel';
import { AiClosedLoopPanel } from './components/AiClosedLoopPanel';
import { IncidentLogTable } from './components/IncidentLogTable';
import { NodeDetailModal } from './components/NodeDetailModal';

export default function App() {
  // Navigation & Tabs
  const [activeTab, setActiveTab] = useState<string>('topology');
  const [themeColor, setThemeColor] = useState<'cyan' | 'blue' | 'emerald'>('cyan');

  // Network State
  const [nodes, setNodes] = useState<NetworkNode[]>(INITIAL_NODES);
  const [links, setLinks] = useState<NetworkLink[]>(INITIAL_LINKS);
  const [wanMetrics, setWanMetrics] = useState<WANPathMetric[]>(INITIAL_WAN_METRICS);

  // Selected Node for Detail Drawer
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);

  // Active Fault Scenario execution
  const [activeFaultScenario, setActiveFaultScenario] = useState<FaultScenario | null>(null);
  const [executingStage, setExecutingStage] = useState<string>('');
  const [measuredMttr, setMeasuredMttr] = useState<number | undefined>(undefined);

  // AI & PPO State Vector (8 dimensions)
  const [ppoStateVector, setPpoStateVector] = useState<PPOStateVector>({
    cpu: 24,
    resMem: 38,
    virtMem: 45,
    flowsSent: 820,
    flowErrors: 0,
    connections: 18,
    disconnections: 0,
    portsDown: 0,
  });

  // PPO Action Output
  const [ppoAction, setPpoAction] = useState<PPOActionOutput>({
    actionId: 0,
    actionName: 'No-op (Giữ nguyên)',
    probabilities: [0.94, 0.02, 0.01, 0.03],
    reward: 1,
    confidence: 0.98,
  });

  // Safety Layer Audit
  const [safetyAudit, setSafetyAudit] = useState<SafetyLayerAudit>({
    policyApproved: true,
    confidenceScore: 0.98,
    riskLevel: 'LOW',
    blastRadiusPercent: 0,
    rollbackPlanReady: true,
    notes: 'Toàn bộ thông số mạng nằm trong ngưỡng tiêu chuẩn.',
  });

  // Incident Logs Audit Trail
  const [incidentLogs, setIncidentLogs] = useState<IncidentLog[]>([
    {
      id: 'log-1',
      timestamp: '07:15:00',
      title: 'Khởi tạo Topology Mininet 3 Chi nhánh + Data Center',
      severity: 'SUCCESS',
      stage: 'RESOLVED',
      message: 'Bản vẽ kiến trúc tải thành công 22 OVS Switches, 88 Endpoints và 5 kênh WAN. Faucet SDN & Keepalived hoạt động bình thường.',
      targetSite: 'Global',
    },
    {
      id: 'log-2',
      timestamp: '07:15:05',
      title: 'Kích hoạt Telemetry Probe Engine & Prometheus Exporter',
      severity: 'INFO',
      stage: 'RESOLVED',
      message: 'Scrape interval thiết lập 2s cho Faucet port stats và ICMP/iperf WAN probes.',
      targetSite: 'Data Center',
      targetDevice: 'DC-MON01 (:9090)',
    },
  ]);

  // Telemetry real-time pulse simulation
  useEffect(() => {
    const pulseInterval = setInterval(() => {
      setWanMetrics((prev) =>
        prev.map((item) => {
          if (item.status === 'DOWN') return item;
          const deltaTraffic = (Math.random() - 0.5) * 2;
          const newTraffic = Math.max(2, Math.min(item.capacityMbps * 0.95, item.throughputMbps + deltaTraffic));
          const newUtil = (newTraffic / item.capacityMbps) * 100;
          return {
            ...item,
            throughputMbps: parseFloat(newTraffic.toFixed(1)),
            utilizationPercent: parseFloat(newUtil.toFixed(1)),
          };
        })
      );
    }, 3000);

    return () => clearInterval(pulseInterval);
  }, []);

  // Handler: Reset Network to Clean Healthy State
  const handleResetNetwork = useCallback(() => {
    setNodes(INITIAL_NODES);
    setLinks(INITIAL_LINKS);
    setWanMetrics(INITIAL_WAN_METRICS);
    setActiveFaultScenario(null);
    setExecutingStage('');
    setMeasuredMttr(undefined);

    setPpoStateVector({
      cpu: 24,
      resMem: 38,
      virtMem: 45,
      flowsSent: 820,
      flowErrors: 0,
      connections: 18,
      disconnections: 0,
      portsDown: 0,
    });

    setPpoAction({
      actionId: 0,
      actionName: 'No-op (Giữ nguyên)',
      probabilities: [0.95, 0.02, 0.01, 0.02],
      reward: 1,
      confidence: 0.99,
    });

    setSafetyAudit({
      policyApproved: true,
      confidenceScore: 0.99,
      riskLevel: 'LOW',
      blastRadiusPercent: 0,
      rollbackPlanReady: true,
      notes: 'Mạng đã được khôi phục về trạng thái ban đầu ổn định 100%.',
    });

    const now = new Date().toLocaleTimeString('vi-VN', { hour12: false });
    setIncidentLogs((prev) => [
      {
        id: `reset-${Date.now()}`,
        timestamp: now,
        title: 'Thực hiện Reset Toàn Mạng Về Trạng Thái Bình Thường',
        severity: 'SUCCESS',
        stage: 'RESOLVED',
        message: 'Tất cả các cổng, router VRRP, đường WAN và bảng Flow Table đã được nạp lại cấu hình chuẩn.',
        targetSite: 'Global',
      },
      ...prev,
    ]);
  }, []);

  // Handler: Fault Injection & Automated Closed-Loop Self-Healing Sequence
  const handleInjectFault = useCallback((scenario: FaultScenario) => {
    setActiveFaultScenario(scenario);
    setExecutingStage('1. DETECT (Prometheus Anomaly)');
    setMeasuredMttr(undefined);
    const now = new Date().toLocaleTimeString('vi-VN', { hour12: false });

    // Step 0: Apply Fault State to Data Plane
    if (scenario.id === 'F01') {
      // Access Link NT-ACC02 Down
      setNodes((prev) =>
        prev.map((n) => (n.id === 'NT-ACC02' ? { ...n, status: 'OFFLINE' } : n))
      );
      setLinks((prev) =>
        prev.map((l) => (l.id === 'L-NT-4' ? { ...l, status: 'DOWN', lossPercent: 100 } : l))
      );
      setPpoStateVector((prev) => ({ ...prev, portsDown: 1 }));
    } else if (scenario.id === 'F02') {
      // Distribution VRRP Master NT-DIST01 Down
      setNodes((prev) =>
        prev.map((n) => {
          if (n.id === 'NT-DIST01') return { ...n, status: 'OFFLINE', vrrpRole: 'NONE' };
          if (n.id === 'NT-DIST02') return { ...n, vrrpRole: 'MASTER' };
          return n;
        })
      );
      setPpoStateVector((prev) => ({ ...prev, disconnections: 1 }));
    } else if (scenario.id === 'F04') {
      // MPLS Down -> Reroute to 5G
      setWanMetrics((prev) =>
        prev.map((w) =>
          w.transport === 'MPLS'
            ? { ...w, status: 'DOWN', lossPercent: 100, latencyMs: 999, mosVoip: 1.0, throughputMbps: 0, utilizationPercent: 0 }
            : w.transport === '5G'
            ? { ...w, throughputMbps: 92, utilizationPercent: 46 } // absorb traffic
            : w
        )
      );
      setLinks((prev) =>
        prev.map((l) => (l.transport === 'MPLS' ? { ...l, status: 'DOWN', lossPercent: 100 } : l))
      );
    } else if (scenario.id === 'F07') {
      // 5G Degradation (loss > 5%)
      setWanMetrics((prev) =>
        prev.map((w) =>
          w.transport === '5G'
            ? { ...w, status: 'DEGRADED', lossPercent: 6.5, jitterMs: 25, mosVoip: 3.2 }
            : w
        )
      );
    } else if (scenario.id === 'F09') {
      // WAN Congestion
      setWanMetrics((prev) =>
        prev.map((w) =>
          w.transport === 'MPLS'
            ? { ...w, status: 'CONGESTED', throughputMbps: 88, utilizationPercent: 88, jitterMs: 40, mosVoip: 2.8 }
            : w
        )
      );
    } else if (scenario.id === 'F11') {
      // Web server crash
      setNodes((prev) =>
        prev.map((n) => (n.id === 'DC-SERVERS' ? { ...n, status: 'DEGRADED' } : n))
      );
    } else if (scenario.id === 'P1') {
      // Proactive traffic spike
      setWanMetrics((prev) =>
        prev.map((w) =>
          w.transport === 'MPLS' ? { ...w, throughputMbps: 65, utilizationPercent: 65 } : w
        )
      );
    }

    // Add Detection Log
    setIncidentLogs((prev) => [
      {
        id: `inc-${Date.now()}-1`,
        timestamp: now,
        faultId: scenario.id,
        title: `Phát Hiện Sự Cố: ${scenario.name}`,
        severity: 'CRITICAL',
        stage: 'DETECT',
        message: `Prometheus & Telemetry Probes ghi nhận: ${scenario.detectionMechanism}`,
        targetSite: String(scenario.targetSite),
        targetDevice: scenario.targetDevice,
      },
      ...prev,
    ]);

    // Timeline step 1: RCA Engine (1.2s)
    setTimeout(() => {
      setExecutingStage('2. RCA (Root Cause Analysis)');
      setIncidentLogs((prev) => [
        {
          id: `inc-${Date.now()}-2`,
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour12: false }),
          faultId: scenario.id,
          title: `RCA Xác Định Nguyên Nhân Gốc`,
          severity: 'WARNING',
          stage: 'RCA',
          message: `${scenario.rootCauseAnalysis}`,
          targetSite: String(scenario.targetSite),
          targetDevice: scenario.targetDevice,
        },
        ...prev,
      ]);
    }, 1200);

    // Timeline step 2: Safety Layer Audit (2.2s)
    setTimeout(() => {
      setExecutingStage('3. SAFETY (Policy Audit Check)');
      setSafetyAudit({
        policyApproved: true,
        confidenceScore: 0.97,
        riskLevel: 'LOW',
        blastRadiusPercent: 1.1,
        rollbackPlanReady: true,
        notes: `Phê duyệt tự động cho sự cố ${scenario.id}: Tác động gói gọn dưới 30% bán kính mạng.`,
      });
      setIncidentLogs((prev) => [
        {
          id: `inc-${Date.now()}-3`,
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour12: false }),
          faultId: scenario.id,
          title: `Safety Layer Phê Duyệt Kế Hoạch`,
          severity: 'INFO',
          stage: 'SAFETY',
          message: `Confidence: 97% >= 80%, Blast Radius: 1.1% <= 30%. Cho phép bộ điều khiển tự động thực thi.`,
          targetSite: String(scenario.targetSite),
        },
        ...prev,
      ]);
    }, 2200);

    // Timeline step 3: PPO RL / SD-WAN Execution (3.2s)
    setTimeout(() => {
      setExecutingStage('4. EXECUTE (PPO / SD-WAN Controller)');

      let chosenAction: 0 | 1 | 2 | 3 = 1;
      let actionName = 'Reset Port';
      let probs: [number, number, number, number] = [0.05, 0.92, 0.01, 0.02];

      if (scenario.id === 'F02') {
        chosenAction = 0;
        actionName = 'No-op / Let VRRP Failover';
        probs = [0.95, 0.02, 0.01, 0.02];
      } else if (scenario.id === 'F12') {
        chosenAction = 2;
        actionName = 'Restart Switch / Reload Controller Process';
        probs = [0.03, 0.05, 0.89, 0.03];
      }

      setPpoAction({
        actionId: chosenAction,
        actionName: actionName,
        probabilities: probs,
        reward: chosenAction === 1 ? 10 : chosenAction === 2 ? 20 : 1,
        confidence: 0.97,
        targetDpid: scenario.targetDevice,
      });

      // Node enters RECOVERING state
      setNodes((prev) =>
        prev.map((n) =>
          n.status === 'OFFLINE' ? { ...n, status: 'RECOVERING' } : n
        )
      );

      setIncidentLogs((prev) => [
        {
          id: `inc-${Date.now()}-4`,
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour12: false }),
          faultId: scenario.id,
          title: `Thực Thi Hành Động: ${scenario.ppoAction}`,
          severity: 'INFO',
          stage: 'EXECUTE',
          message: `Controller phát lệnh OpenFlow / SD-WAN Policy: ${scenario.recoveryFlow}`,
          targetSite: String(scenario.targetSite),
        },
        ...prev,
      ]);
    }, 3200);

    // Timeline step 4: Verify & Recovered (4.8s)
    setTimeout(() => {
      setExecutingStage('5. RESOLVED (Verify & Restore)');
      const finalMttr = scenario.type === 'Proactive' ? 0.0 : 4.6;
      setMeasuredMttr(finalMttr);

      // Restore states
      setNodes((prev) =>
        prev.map((n) => ({
          ...n,
          status: 'ONLINE',
          vrrpRole: n.id === 'NT-DIST01' ? 'MASTER' : n.id === 'NT-DIST02' ? 'BACKUP' : n.vrrpRole,
        }))
      );
      setLinks((prev) => prev.map((l) => ({ ...l, status: 'UP', lossPercent: 0 })));
      setWanMetrics(INITIAL_WAN_METRICS);

      setPpoStateVector({
        cpu: 24,
        resMem: 38,
        virtMem: 45,
        flowsSent: 840,
        flowErrors: 0,
        connections: 18,
        disconnections: 0,
        portsDown: 0,
      });

      setIncidentLogs((prev) => [
        {
          id: `inc-${Date.now()}-5`,
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour12: false }),
          faultId: scenario.id,
          title: `Sự Cố Đã Được Tự Phục Hồi Thành Công`,
          severity: 'SUCCESS',
          stage: 'RESOLVED',
          message: `Toàn bộ lưu lượng và liên kết đã hoạt động danh nghĩa trở lại. MTTR đo được: ${finalMttr}s.`,
          mttrSec: finalMttr,
          targetSite: String(scenario.targetSite),
        },
        ...prev,
      ]);
    }, 4800);
  }, []);

  // Handler: Toggle Individual Node Status for Interactive Testing
  const handleToggleNodeStatus = useCallback((nodeId: string) => {
    setNodes((prev) =>
      prev.map((n) => {
        if (n.id === nodeId) {
          const newStatus = n.status === 'ONLINE' ? 'OFFLINE' : 'ONLINE';
          return { ...n, status: newStatus };
        }
        return n;
      })
    );

    setSelectedNode((prev) =>
      prev && prev.id === nodeId
        ? { ...prev, status: prev.status === 'ONLINE' ? 'OFFLINE' : 'ONLINE' }
        : prev
    );
  }, []);

  // Computed Metrics
  const onlineCount = nodes.filter((n) => n.status === 'ONLINE').length;
  const activeFaultsCount = nodes.filter((n) => n.status === 'OFFLINE' || n.status === 'DEGRADED').length;

  return (
    <div className={`min-h-screen text-slate-100 flex flex-col font-sans transition-colors duration-300 ${
      themeColor === 'blue'
        ? 'bg-[#060b18] selection:bg-blue-500 selection:text-white'
        : themeColor === 'emerald'
        ? 'bg-[#05110d] selection:bg-emerald-500 selection:text-slate-950'
        : 'bg-[#070b14] selection:bg-cyan-500 selection:text-slate-950'
    }`}>
      {/* NOC Header Bar */}
      <NocHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onlineCount={onlineCount}
        totalNodes={nodes.length}
        activeFaultsCount={activeFaultsCount}
        averageMttr={3.8}
        slaPercent={99.98}
        themeColor={themeColor}
        setThemeColor={setThemeColor}
      />

      {/* Main Viewport Workspace */}
      <main className="flex-1 p-4 lg:p-6 max-w-[1600px] w-full mx-auto">
        {/* Tab 1: Architectural SVG Blueprint Topology Canvas */}
        {activeTab === 'topology' && (
          <div className="space-y-4">
            <NetworkBlueprintTopology
              nodes={nodes}
              links={links}
              onSelectNode={(node) => setSelectedNode(node)}
              selectedNodeId={selectedNode?.id}
              activeFaultId={activeFaultScenario?.id}
            />
          </div>
        )}

        {/* Tab 2: Interactive Scenario Simulation Studio (14 Scenarios) */}
        {activeTab === 'scenarios' && (
          <InteractiveScenarioStudio
            scenarios={FAULT_SCENARIOS}
            activeScenarioId={activeFaultScenario?.id}
            onInjectFault={handleInjectFault}
            onResetNetwork={handleResetNetwork}
            themeColor={themeColor}
          />
        )}

        {/* Tab 3: 5 WAN Transports Monitor */}
        {activeTab === 'wan' && (
          <WanMonitorPanel wanMetrics={wanMetrics} />
        )}

        {/* Tab 4: AI & PPO RL Brain */}
        {activeTab === 'ai-engine' && (
          <AiClosedLoopPanel
            stateVector={ppoStateVector}
            actionOutput={ppoAction}
            safetyAudit={safetyAudit}
          />
        )}

        {/* Tab 5: Incident Audit Logs */}
        {activeTab === 'logs' && (
          <IncidentLogTable
            logs={incidentLogs}
            onClearLogs={() => setIncidentLogs([])}
          />
        )}
      </main>

      {/* Node Detail Modal / Drawer */}
      <NodeDetailModal
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onToggleNodeStatus={handleToggleNodeStatus}
      />
    </div>
  );
}
