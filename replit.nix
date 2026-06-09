{ pkgs }: {
	deps = [
	 pkgs.glibcLocales
	 pkgs.glibc
	 pkgs.libiconv
	 pkgs.python313Full
	 pkgs.uv
	];
	env = {
		PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
			# Needed for pandas / numpy
			pkgs.stdenv.cc.cc.lib
			pkgs.zlib
			# Needed for matplotlib
			pkgs.xorg.libX11
		];
		PYTHONHOME = "${pkgs.python313Full}";
		PYTHONBIN = "${pkgs.python313Full}/bin/python3.13";
		LANG = "en_US.UTF-8";
	};
}
