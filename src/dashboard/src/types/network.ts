export type NodeStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'RECOVERING';
export type SiteId = 'baoloc' | 'nhatrang' | 'hcm' | 'datacenter';
export type NodeRole = 'core' | 'dist' | 'access' | 'gateway' | 'server' | 'spine' | 'leaf' | 'host';

export interface NetworkInterface {
  name: string;
  ip?: string;
  mac?: string;
  status: 'UP' | 'DOWN';
  speedMbps: number;
  rxBytes: number;
  txBytes: number;
}

export interface NetworkNode {
  id: string;
  name: string;
  site: SiteId;
  role: NodeRole;
  ip: string;
  vlan?: number | string;
  mac?: string;
  status: NodeStatus;
  cpuPercent: number;
  memoryPercent: number;
  interfaces: NetworkInterface[];
  flowCount?: number;
  vrrpRole?: 'MASTER' | 'BACKUP' | 'NONE';
  vrrpPriority?: number;
  ospfNeighbors?: string[];
  description: string;
  x: number;
  y: number;
  parent?: string;
}

export type LinkTransport = 'MPLS' | '5G' | 'Internet' | 'LTE' | 'VPN' | 'INTERNAL_LAN' | 'BACKBONE';
export type LinkStatus = 'UP' | 'DOWN' | 'CONGESTED' | 'STEERED' | 'FAILOVER';

export interface NetworkLink {
  id: string;
  source: string;
  target: string;
  transport: LinkTransport;
  status: LinkStatus;
  bandwidthMbps: number;
  currentTrafficMbps: number;
  latencyMs: number;
  lossPercent: number;
  jitterMs: number;
  utilizationPercent: number;
  activeTrafficClasses?: string[];
}

export type FaultId = 
  | 'F01' | 'F02' | 'F03' | 'F04' | 'F05' | 'F06' 
  | 'F07' | 'F08' | 'F09' | 'F10' | 'F11' | 'F12' 
  | 'P1'  | 'P2';

export interface FaultScenario {
  id: FaultId;
  name: string;
  type: 'Reactive' | 'Proactive';
  category: 'LAN (SDN)' | 'WAN (SD-WAN)' | 'DC (Service)' | 'AI / Multi-Metric';
  controller: 'Faucet / Ryu SDN' | 'Custom SD-WAN (Python)' | 'HAProxy LB' | 'AI Multi-Agent';
  targetSite: SiteId | 'WAN Backbone' | 'Global';
  targetDevice: string;
  symptom: string;
  detectionMechanism: string;
  rootCauseAnalysis: string;
  ppoAction: string;
  recoveryFlow: string;
  targetMttr: string;
  commandSnippet: string;
}

export interface PPOStateVector {
  cpu: number;          // C_cpu
  resMem: number;       // C_res_mem
  virtMem: number;      // C_virt_mem
  flowsSent: number;    // f_sent
  flowErrors: number;   // f_err
  connections: number;  // f_conn
  disconnections: number; // f_disc
  portsDown: number;    // P_down
}

export interface PPOActionOutput {
  actionId: 0 | 1 | 2 | 3;
  actionName: string;
  probabilities: [number, number, number, number];
  reward: number;
  confidence: number;
  targetDpid?: string;
  targetPort?: string | number;
}

export interface SafetyLayerAudit {
  policyApproved: boolean;
  confidenceScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  blastRadiusPercent: number;
  rollbackPlanReady: boolean;
  notes: string;
}

export interface IncidentLog {
  id: string;
  timestamp: string;
  faultId?: FaultId;
  title: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'SUCCESS';
  stage: 'DETECT' | 'RCA' | 'SAFETY' | 'EXECUTE' | 'VERIFY' | 'RESOLVED';
  message: string;
  mttrSec?: number;
  targetSite?: string;
  targetDevice?: string;
}

export interface WANPathMetric {
  transport: 'MPLS' | '5G' | 'Internet' | 'LTE' | 'VPN';
  name: string;
  status: 'OPTIMAL' | 'DEGRADED' | 'DOWN' | 'CONGESTED';
  capacityMbps: number;
  throughputMbps: number;
  latencyMs: number;
  baseLatencyMs: number;
  lossPercent: number;
  jitterMs: number;
  utilizationPercent: number;
  mosVoip: number;
  routedServices: string[];
}
