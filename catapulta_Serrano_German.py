"""
catapulta.py
Simulación orientada a objetos de una mini-catapulta segura.
Modelo:
 - Energía almacenada en bandas: E = 0.5 * K * x^2  (K = n_bandas * k_band)
 - Energía útil = eficiencia * E
 - Velocidad inicial v = sqrt(2 * Energía_útil / m)
 - Alcance (ángulo theta): R = (v^2 * sin(2*theta)) / g   (sin 2θ en radianes)
"""

import math
from statistics import mean

G = 9.81  # gravedad m/s^2

class Projectile:
    def __init__(self, mass_kg: float, name: str = "proyectil blando"):
        if mass_kg <= 0:
            raise ValueError("La masa debe ser positiva.")
        self.mass = mass_kg
        self.name = name

class BandSystem:
    """
    Representa el conjunto de bandas elásticas.
    k_band: constante aproximada por banda (N/m)
    n_bands: número de bandas en paralelo
    """
    def __init__(self, k_band: float = 200.0, n_bands: int = 4):
        if k_band <= 0 or n_bands < 1:
            raise ValueError("k_band > 0 y n_bands >= 1")
        self.k_band = k_band
        self.n_bands = n_bands

    @property
    def K_total(self) -> float:
        return self.k_band * self.n_bands

class CatapultArm:
    """
    Opcionalmente modelamos la longitud del brazo (m) por referencia.
    En esta simulación simple no convertimos rotación => energía (suponemos
    que la energía elástica se transfiere con un factor 'eficiencia').
    """
    def __init__(self, length_m: float = 0.2):
        if length_m <= 0:
            raise ValueError("La longitud del brazo debe ser positiva.")
        self.length = length_m

class Catapult:
    def __init__(self,
                 band_system: BandSystem,
                 arm: CatapultArm = CatapultArm(),
                 eficiencia: float = 0.35):
        """
        eficiencia: fracción (0..1) de energía elástica que pasa a energía cinética útil
                    (pérdidas por fricción, flexión, ineficiencia de acople)
        """
        if not (0 < eficiencia <= 1):
            raise ValueError("eficiencia debe estar en (0,1].")
        self.bands = band_system
        self.arm = arm
        self.eficiencia = eficiencia
        self.loaded_projectile = None
        self.pull_distance = 0.0  # desplazamiento x en metros (cómo de lejos tiras hacia atrás)

    def load(self, projectile: Projectile):
        self.loaded_projectile = projectile

    def set_pull(self, distance_m: float):
        if distance_m < 0:
            raise ValueError("La distancia de tracción debe ser >= 0")
        self.pull_distance = distance_m

    def stored_energy(self) -> float:
        """E = 0.5 * K_total * x^2"""
        K = self.bands.K_total
        x = self.pull_distance
        return 0.5 * K * x * x

    def launch_velocity(self) -> float:
        """v = sqrt( 2 * (eficiencia * E) / m )"""
        if self.loaded_projectile is None:
            raise RuntimeError("No hay proyectil cargado.")
        E_stored = self.stored_energy()
        E_useful = self.eficiencia * E_stored
        m = self.loaded_projectile.mass
        if E_useful <= 0:
            return 0.0
        return math.sqrt(2.0 * E_useful / m)

    def range_at_angle(self, angle_deg: float) -> float:
        """R = (v^2 * sin(2*theta)) / g  (ángulo en grados)"""
        v = self.launch_velocity()
        theta = math.radians(angle_deg)
        return (v * v * math.sin(2 * theta)) / G

    def simulate_launch(self, angle_deg: float):
        """Devuelve un dict con resultados numéricos"""
        v = self.launch_velocity()
        R = self.range_at_angle(angle_deg)
        return {
            "proyectil": self.loaded_projectile.name if self.loaded_projectile else None,
            "masa_kg": self.loaded_projectile.mass if self.loaded_projectile else None,
            "pull_m": self.pull_distance,
            "K_total_N_per_m": self.bands.K_total,
            "energia_almacenada_J": self.stored_energy(),
            "energia_util_J": self.eficiencia * self.stored_energy(),
            "velocidad_m_s": v,
            "angulo_deg": angle_deg,
            "alcance_m": R
        }

class Experiment:
    """Permite correr varios lanzamientos y promediar resultados"""
    def __init__(self, catapult: Catapult):
        self.cat = catapult

    def run_trials(self, angle_deg: float, n: int = 5):
        if n < 1:
            raise ValueError("n debe ser >= 1")
        results = []
        for _ in range(n):
            res = self.cat.simulate_launch(angle_deg)
            results.append(res["alcance_m"])
        return {
            "n": n,
            "angle_deg": angle_deg,
            "distancias": results,
            "media_m": mean(results)
        }

# --------------------------
# Ejemplo de uso (se ejecuta si corres este archivo directamente)
# --------------------------
if __name__ == "__main__":
    # Valores iniciales seguros y realistas para una mini-catapulta casera:
    # - proyectil blando: 5 g (0.005 kg)
    # - k_band aproximado: 200 N/m por banda
    # - 4 bandas en paralelo => K_total = 800 N/m
    # - tirar hacia atrás ~0.03 m (3 cm)
    proj = Projectile(0.005, "pompon 5g")
    bands = BandSystem(k_band=200.0, n_bands=4)
    arm = CatapultArm(length_m=0.18)
    cat = Catapult(bands, arm, eficiencia=0.35)

    cat.load(proj)
    cat.set_pull(0.03)  # 3 cm, valor de ejemplo

    # Probar ángulo óptimo cercano a 45°
    angle = 45.0
    sim = cat.simulate_launch(angle)
    print("Simulación de lanzamiento (un solo tiro):")
    for k, v in sim.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    # Ejecutar varias pruebas y promediar
    exp = Experiment(cat)
    summary = exp.run_trials(angle_deg=45.0, n=5)
    print("\nResumen de ensayo (5 repeticiones):")
    print(f"  ángulo: {summary['angle_deg']}°")
    print(f"  distancias (m): {[round(d,3) for d in summary['distancias']]}")
    print(f"  distancia media (m): {summary['media_m']:.3f}")
