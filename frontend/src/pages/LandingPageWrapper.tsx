import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import LandingPage from "./LandingPage";
import { subscribeToAuthChanges } from "../services/auth";
import type { User as FirebaseUser } from "firebase/auth";

export const LandingPageWrapper: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<FirebaseUser | null>(null);

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((u) => {
      setUser(u);
    });
    return () => {
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, []);

  return (
    <div style={{ width: "100%", height: "100%", minHeight: "100vh", backgroundColor: "#0A0B10" }}>
      <LandingPage
        user={user}
        onConnectToDashboard={() => navigate("/dashboard")}
      />
    </div>
  );
};

export default LandingPageWrapper;
