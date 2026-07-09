import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { AddCard } from "./pages/AddCard";
import { AddPurchase } from "./pages/AddPurchase";
import { Statement } from "./pages/Statement";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cards/new" element={<AddCard />} />
        <Route path="/cards/:productId/purchases/new" element={<AddPurchase />} />
        <Route path="/cards/:productId/purchases/:purchaseId" element={<Statement />} />
      </Routes>
    </Layout>
  );
}

export default App;
