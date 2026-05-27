{
  description = "Entorno de desarrollo para Python 3.12";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [ pkgs.mariadb ];
        packages = with pkgs; [
          python312
          python312Packages.pip
          python312Packages.virtualenv
          zlib
          stdenv.cc.cc.lib
        ];

        shellHook = ''
          # Crea el entorno virtual si no existe
          if [ ! -d ".venv" ]; then
            echo "Creando entorno virtual de Python..."
            python3 -m venv .venv
          fi

          # Activa el entorno virtual
          source .venv/bin/activate

          # Soluciona problemas de enlaces dinámicos (.so) típicos de pip en NixOS
          export LD_LIBRARY_PATH="${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"


          # Define local directory for DB data
          export MYSQL_BASEDIR=${pkgs.mariadb}
          export MYSQL_HOME=$PWD/.mariadb
          export MYSQL_DATADIR=$MYSQL_HOME/data
          export MYSQL_UNIX_PORT=$MYSQL_HOME/mysql.sock
          export MYSQL_PID_FILE=$MYSQL_HOME/mysql.pid

          if [ ! -d "$MYSQL_DATADIR" ]; then
            mysql_install_db --datadir=$MYSQL_DATADIR --basedir=$MYSQL_BASEDIR --auth-root-authentication-method=normal
          fi

          mysqld --datadir=$MYSQL_DATADIR --pid-file=$MYSQL_PID_FILE --socket=$MYSQL_UNIX_PORT --skip-networking &

          until mysqladmin ping --socket=$MYSQL_UNIX_PORT --silent; do
            echo "Waiting for MariaDB..."
            sleep 1
          done

          echo "MariaDB is ready! Socket: $MYSQL_UNIX_PORT"

          trap "mysqladmin -u root --socket=$MYSQL_UNIX_PORT shutdown"

          echo "Entorno de Python 3.12 listo."
        '';
      };
    };

}
