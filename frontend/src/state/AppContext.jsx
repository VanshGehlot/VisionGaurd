import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  getEvents,
  getHealth,
  getMetrics,
  getOperationsAlert,
  getReport,
} from "../lib/api";

const AppContext = createContext(null);
const initialServiceStatus = {
  health: "idle",
  metrics: "idle",
  events: "idle",
  report: "idle",
  operationsAlert: "idle",
};

export function AppProvider({ children }) {
  const [frontendDemoMode, setFrontendDemoMode] = useState(false);
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [report, setReport] = useState("");
  const [operationsAlert, setOperationsAlert] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [serviceStatus, setServiceStatus] = useState(initialServiceStatus);
  const [lastUpdated, setLastUpdated] = useState("");

  async function refreshSystemData(limit = 16) {
    setLoading(true);
    try {
      const [
        healthResult,
        metricsResult,
        eventsResult,
        reportResult,
        alertResult,
      ] = await Promise.allSettled([
        getHealth(),
        getMetrics(),
        getEvents(limit),
        getReport(),
        getOperationsAlert(),
      ]);

      const nextServiceStatus = {
        health: healthResult.status === "fulfilled" ? "ok" : "error",
        metrics: metricsResult.status === "fulfilled" ? "ok" : "error",
        events: eventsResult.status === "fulfilled" ? "ok" : "error",
        report: reportResult.status === "fulfilled" ? "ok" : "error",
        operationsAlert: alertResult.status === "fulfilled" ? "ok" : "error",
      };

      setServiceStatus(nextServiceStatus);
      setHealth(healthResult.status === "fulfilled" ? healthResult.value : null);
      setMetrics(metricsResult.status === "fulfilled" ? metricsResult.value : null);
      setEvents(eventsResult.status === "fulfilled" ? eventsResult.value.events || [] : []);
      setReport(reportResult.status === "fulfilled" ? reportResult.value.report || "" : "");
      setOperationsAlert(alertResult.status === "fulfilled" ? alertResult.value.alert || "" : "");

      const failedServices = Object.entries(nextServiceStatus)
        .filter(([, status]) => status === "error")
        .map(([key]) => key);

      if (!failedServices.length) {
        setError("");
      } else if (failedServices.length === Object.keys(nextServiceStatus).length) {
        setError("Live system data is unavailable right now. VisionGuard is showing a degraded UI state.");
      } else {
        setError("Some live system panels are unavailable right now. Data shown below may be incomplete.");
      }

      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error("VisionGuard system refresh failed", err);
      setServiceStatus({
        health: "error",
        metrics: "error",
        events: "error",
        report: "error",
        operationsAlert: "error",
      });
      setHealth(null);
      setMetrics(null);
      setEvents([]);
      setReport("");
      setOperationsAlert("");
      setError("Live system data is unavailable right now. VisionGuard is showing a degraded UI state.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshSystemData();
  }, []);

  const value = useMemo(
    () => ({
      frontendDemoMode,
      setFrontendDemoMode,
      health,
      metrics,
      events,
      report,
      operationsAlert,
      loading,
      error,
      serviceStatus,
      lastUpdated,
      refreshSystemData,
    }),
    [
      frontendDemoMode,
      health,
      metrics,
      events,
      report,
      operationsAlert,
      loading,
      error,
      serviceStatus,
      lastUpdated,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const value = useContext(AppContext);
  if (!value) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return value;
}
