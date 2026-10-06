/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class DentalDashboard extends Component {
    static template = "smartdesk_dental_management.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, loading: true });
        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("dental.dashboard", "get_data", []);
        this.state.loading = false;
    }

    open(xmlid) {
        this.action.doAction(`smartdesk_dental_management.${xmlid}`);
    }

    openAppointment(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "dental.appointment",
            res_id: id,
            views: [[false, "form"]],
        });
    }

    money(value) {
        const n = Math.round(value || 0).toLocaleString();
        return `${this.state.data.currency || ""}${n}`;
    }

    get maxRevenue() {
        return Math.max(1, ...this.state.data.revenue.map((r) => r.value));
    }

    barHeight(value) {
        return Math.max(2, Math.round((value / this.maxRevenue) * 100));
    }

    get donutStyle() {
        const items = this.state.data.by_state;
        const total = items.reduce((s, i) => s + i.count, 0);
        if (!total) {
            return "background:#e5e7eb";
        }
        let acc = 0;
        const stops = items.map((i) => {
            const from = (acc / total) * 100;
            acc += i.count;
            return `${i.color} ${from}% ${(acc / total) * 100}%`;
        });
        return `background:conic-gradient(${stops.join(",")})`;
    }

    get statusTotal() {
        return this.state.data.by_state.reduce((s, i) => s + i.count, 0);
    }

    get maxProcedure() {
        return Math.max(1, ...this.state.data.top_procedures.map((p) => p.amount));
    }

    get maxDentist() {
        return Math.max(1, ...this.state.data.dentist_load.map((d) => d.count));
    }
}

registry.category("actions").add("dental_dashboard", DentalDashboard);
