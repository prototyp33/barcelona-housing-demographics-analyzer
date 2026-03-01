#!/bin/bash
# Setup script para configurar el entorno de Jupyter

echo "🔧 Configurando entorno de Jupyter para Barcelona Housing Analytics"
echo ""

# Agregar Python user bin al PATH si no está
PYTHON_USER_BIN="$HOME/Library/Python/3.12/bin"

if [[ ":$PATH:" != *":$PYTHON_USER_BIN:"* ]]; then
    echo "📍 Agregando $PYTHON_USER_BIN al PATH..."
    export PATH="$PYTHON_USER_BIN:$PATH"
    echo "✅ PATH actualizado"
else
    echo "✅ PATH ya contiene $PYTHON_USER_BIN"
fi

# Verificar instalaciones
echo ""
echo "📦 Verificando instalaciones..."
echo ""

if command -v jupyter &> /dev/null; then
    echo "✅ Jupyter: $(jupyter --version | head -1)"
else
    echo "❌ Jupyter no encontrado"
fi

if python3 -c "import scipy" 2>/dev/null; then
    SCIPY_VERSION=$(python3 -c "import scipy; print(scipy.__version__)")
    echo "✅ scipy: $SCIPY_VERSION"
else
    echo "❌ scipy no instalado"
fi

if python3 -c "import pandas" 2>/dev/null; then
    PANDAS_VERSION=$(python3 -c "import pandas; print(pandas.__version__)")
    echo "✅ pandas: $PANDAS_VERSION"
else
    echo "❌ pandas no instalado"
fi

if python3 -c "import numpy" 2>/dev/null; then
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
    echo "✅ numpy: $NUMPY_VERSION"
else
    echo "❌ numpy no instalado"
fi

echo ""
echo "🚀 Para usar Jupyter, ejecuta:"
echo ""
echo "   export PATH=\"$PYTHON_USER_BIN:\$PATH\""
echo "   jupyter lab"
echo ""
echo "O agrega esta línea a tu ~/.zshrc para hacerlo permanente:"
echo ""
echo "   echo 'export PATH=\"$PYTHON_USER_BIN:\$PATH\"' >> ~/.zshrc"
echo ""
