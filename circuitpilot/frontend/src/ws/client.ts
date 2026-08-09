export type BaseEvent = {
  type: string;
  ts: string;
};

export type ChatEvent = BaseEvent & {
  type: "chat";
  role: "assistant" | "user";
  text: string;
};

export type ToolCallStartedEvent = BaseEvent & {
  type: "tool_call_started";
  id: string;
  tool: string;
  args: any;
};

export type ToolCallCompletedEvent = BaseEvent & {
  type: "tool_call_completed";
  id: string;
  result: any;
};

export type FileChangedEvent = BaseEvent & {
  type: "file_changed";
  path: string;
};

export type DRCResultEvent = BaseEvent & {
  type: "drc_result";
  violations: any[];
  clean: boolean;
};

export type ApprovalRequiredEvent = BaseEvent & {
  type: "approval_required";
  id: string;
  action: string;
  detail: string;
};

export type CircuitPilotEvent =
  | ChatEvent
  | ToolCallStartedEvent
  | ToolCallCompletedEvent
  | FileChangedEvent
  | DRCResultEvent
  | ApprovalRequiredEvent;

export class CircuitPilotClient {
  private ws: WebSocket;
  private messageHandlers: Set<(event: CircuitPilotEvent) => void>;

  constructor(url: string) {
    this.ws = new WebSocket(url);
    this.messageHandlers = new Set();

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as CircuitPilotEvent;
        this.messageHandlers.forEach((handler) => handler(data));
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };
  }

  public onMessage(handler: (event: CircuitPilotEvent) => void) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  public sendCommand(text: string) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "user_command", text }));
    }
  }

  public sendApproval(id: string, approved: boolean) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "approval_response", id, approved }));
    }
  }
}
