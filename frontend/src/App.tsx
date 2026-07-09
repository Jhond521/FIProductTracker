import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./lib/auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { AddCard } from "./pages/AddCard";
import { AddPurchase } from "./pages/AddPurchase";
import { Statement } from "./pages/Statement";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/cards/new" element={<AddCard />} />
                  <Route path="/cards/:productId/purchases/new" element={<AddPurchase />} />
                  <Route path="/cards/:productId/purchases/:purchaseId" element={<Statement />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
}

export default App;
