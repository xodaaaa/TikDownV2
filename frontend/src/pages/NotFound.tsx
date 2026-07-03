import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h1 className="text-6xl font-bold text-gray-600">404</h1>
      <p className="text-gray-400 mt-4">Página no encontrada</p>
      <Link
        to="/"
        className="text-accent-400 hover:text-accent-300 mt-6 text-sm underline"
      >
        Volver al Dashboard
      </Link>
    </div>
  );
}
