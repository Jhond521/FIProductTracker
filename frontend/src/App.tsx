import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./lib/auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { AddCard } from "./pages/AddCard";
import { EditCard } from "./pages/EditCard";
import { AddPurchase } from "./pages/AddPurchase";
import { EditPurchase } from "./pages/EditPurchase";
import { Statement } from "./pages/Statement";
import { CardStatements } from "./pages/CardStatements";
import { StatementPeriod } from "./pages/StatementPeriod";
import { Recommendations } from "./pages/Recommendations";

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
                  <Route path="/recommendations" element={<Recommendations />} />
                  <Route path="/cards/new" element={<AddCard />} />
                  <Route path="/cards/:productId/edit" element={<EditCard />} />
                  <Route path="/cards/:productId/purchases/new" element={<AddPurchase />} />
                  <Route
                    path="/cards/:productId/purchases/:purchaseId/edit"
                    element={<EditPurchase />}
                  />
                  <Route path="/cards/:productId/purchases/:purchaseId" element={<Statement />} />
                  <Route path="/cards/:productId/statements" element={<CardStatements />} />
                  <Route
                    path="/cards/:productId/statements/:periodEnd"
                    element={<StatementPeriod />}
                  />
                  <Route
                    path="/cards/:productId/recommendations"
                    element={<Recommendations />}
                  />
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
