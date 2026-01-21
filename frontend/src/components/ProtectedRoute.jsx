// src/components/ProtectedRoute.jsx
import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Loader from "./Loader";

const ProtectedRoute = () => {
  const { token, loading } = useAuth();

  if (loading) {
    return <Loader />;
  }

  return token ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;
