
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```bash
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const SHELL: string;
	export const npm_command: string;
	export const LSCOLORS: string;
	export const SESSION_MANAGER: string;
	export const USER_ZDOTDIR: string;
	export const QT_ACCESSIBILITY: string;
	export const COLORTERM: string;
	export const PYENV_SHELL: string;
	export const npm_package_scripts_generate_types: string;
	export const XDG_CONFIG_DIRS: string;
	export const npm_package_devDependencies__types_node: string;
	export const LESS: string;
	export const XDG_SESSION_PATH: string;
	export const XDG_MENU_PREFIX: string;
	export const npm_package_repository_url: string;
	export const TERM_PROGRAM_VERSION: string;
	export const GTK_IM_MODULE: string;
	export const CLUTTER_BACKEND: string;
	export const npm_package_exports___hooks_import: string;
	export const LANGUAGE: string;
	export const _P9K_TTY: string;
	export const NODE: string;
	export const npm_package_scripts_test_cross_platform_build: string;
	export const LC_ADDRESS: string;
	export const LC_NAME: string;
	export const npm_package_exports___node_polyfills_types: string;
	export const SSH_AUTH_SOCK: string;
	export const npm_package_devDependencies_dts_buddy: string;
	export const P9K_TTY: string;
	export const NODENV_DIR: string;
	export const XMODIFIERS: string;
	export const npm_package_peerDependencies_svelte: string;
	export const DESKTOP_SESSION: string;
	export const LC_MONETARY: string;
	export const SSH_AGENT_PID: string;
	export const NODENV_VERSION: string;
	export const npm_package_exports___import: string;
	export const EDITOR: string;
	export const npm_package_scripts_test_unit: string;
	export const FZF_ALT_C_OPTS: string;
	export const GOENV_SHELL: string;
	export const GTK_MODULES: string;
	export const XDG_SEAT: string;
	export const npm_package_dependencies_sade: string;
	export const PWD: string;
	export const npm_package_devDependencies_vite: string;
	export const XDG_SESSION_DESKTOP: string;
	export const LOGNAME: string;
	export const QT_QPA_PLATFORMTHEME: string;
	export const XDG_SESSION_TYPE: string;
	export const PANEL_GDK_CORE_DEVICE_EVENTS: string;
	export const PNPM_HOME: string;
	export const XAUTHORITY: string;
	export const npm_package_exports___node_import: string;
	export const npm_package_dependencies_cookie: string;
	export const FZF_DEFAULT_COMMAND: string;
	export const VSCODE_GIT_ASKPASS_NODE: string;
	export const npm_package_dependencies_sirv: string;
	export const npm_package_dependencies_tiny_glob: string;
	export const XDG_GREETER_DATA_DIR: string;
	export const npm_package_bugs_url: string;
	export const npm_package_exports___node_types: string;
	export const npm_package_exports___vite_types: string;
	export const VSCODE_INJECTION: string;
	export const GDM_LANG: string;
	export const NODENV_SHELL: string;
	export const HOME: string;
	export const NODENV_ORIG_PATH: string;
	export const LC_PAPER: string;
	export const LANG: string;
	export const npm_package_devDependencies_typescript: string;
	export const LS_COLORS: string;
	export const FZF_CTRL_R_OPTS: string;
	export const XDG_CURRENT_DESKTOP: string;
	export const NODENV_ROOT: string;
	export const npm_package_version: string;
	export const VIRTUAL_ENV: string;
	export const npm_package_files_0: string;
	export const npm_package_scripts_check_all: string;
	export const npm_package_files_1: string;
	export const npm_package_files_2: string;
	export const npm_package_repository_type: string;
	export const npm_package_files_3: string;
	export const npm_package_files_4: string;
	export const npm_package_files_5: string;
	export const npm_package_files_6: string;
	export const npm_package_scripts_test_integration: string;
	export const GIT_ASKPASS: string;
	export const npm_package_exports___vite_import: string;
	export const XDG_SEAT_PATH: string;
	export const npm_package_peerDependencies__sveltejs_vite_plugin_svelte: string;
	export const npm_package_devDependencies__types_set_cookie_parser: string;
	export const npm_package_dependencies_kleur: string;
	export const GOROOT: string;
	export const NODENV_HOOK_PATH: string;
	export const npm_package_devDependencies_rollup: string;
	export const INIT_CWD: string;
	export const CHROME_DESKTOP: string;
	export const CLUTTER_IM_MODULE: string;
	export const npm_package_scripts_test_cross_platform_dev: string;
	export const npm_package_scripts_format: string;
	export const npm_package_dependencies_import_meta_resolve: string;
	export const npm_lifecycle_script: string;
	export const npm_package_description: string;
	export const VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
	export const npm_package_devDependencies__sveltejs_vite_plugin_svelte: string;
	export const XDG_SESSION_CLASS: string;
	export const npm_package_peerDependencies_vite: string;
	export const LC_IDENTIFICATION: string;
	export const TERM: string;
	export const npm_package_name: string;
	export const ZSH: string;
	export const FZF_CTRL_T_COMMAND: string;
	export const VSCODE_NONCE: string;
	export const ZDOTDIR: string;
	export const npm_package_type: string;
	export const USER: string;
	export const npm_config_frozen_lockfile: string;
	export const npm_package_devDependencies_vitest: string;
	export const npm_package_exports___types: string;
	export const FZF_ALT_C_COMMAND: string;
	export const VSCODE_GIT_IPC_HANDLE: string;
	export const npm_package_exports___package_json: string;
	export const npm_package_homepage: string;
	export const FZF_CTRL_T_OPTS: string;
	export const npm_package_dependencies_set_cookie_parser: string;
	export const npm_package_dependencies__types_cookie: string;
	export const DISPLAY: string;
	export const npm_package_exports___node_polyfills_import: string;
	export const npm_lifecycle_event: string;
	export const SHLVL: string;
	export const npm_package_dependencies_magic_string: string;
	export const PAGER: string;
	export const LC_TELEPHONE: string;
	export const GOENV_ROOT: string;
	export const QT_IM_MODULE: string;
	export const LC_MEASUREMENT: string;
	export const _P9K_SSH_TTY: string;
	export const XDG_VTNR: string;
	export const npm_package_devDependencies__types_connect: string;
	export const XDG_SESSION_ID: string;
	export const PAPERSIZE: string;
	export const VIRTUAL_ENV_PROMPT: string;
	export const npm_config_user_agent: string;
	export const npm_package_dependencies_mrmime: string;
	export const npm_package_scripts_lint: string;
	export const PNPM_SCRIPT_SRC_DIR: string;
	export const npm_execpath: string;
	export const npm_package_devDependencies_svelte: string;
	export const npm_package_scripts_test: string;
	export const XDG_RUNTIME_DIR: string;
	export const npm_package_devDependencies_svelte_preprocess: string;
	export const COMPIZ_CONFIG_PROFILE: string;
	export const npm_package_scripts_generate_version: string;
	export const PYENV_ROOT: string;
	export const LC_TIME: string;
	export const npm_package_dependencies_esm_env: string;
	export const npm_package_keywords_4: string;
	export const P9K_SSH: string;
	export const npm_package_keywords_1: string;
	export const npm_package_keywords_0: string;
	export const npm_package_keywords_3: string;
	export const npm_package_keywords_2: string;
	export const npm_package_bin_svelte_kit: string;
	export const VSCODE_GIT_ASKPASS_MAIN: string;
	export const GTK3_MODULES: string;
	export const XDG_DATA_DIRS: string;
	export const npm_package_scripts_check: string;
	export const GDK_BACKEND: string;
	export const PATH: string;
	export const npm_package_dependencies_devalue: string;
	export const GDMSESSION: string;
	export const npm_package_exports___hooks_types: string;
	export const ORIGINAL_XDG_CURRENT_DESKTOP: string;
	export const npm_package_devDependencies__playwright_test: string;
	export const DBUS_SESSION_BUS_ADDRESS: string;
	export const npm_package_license: string;
	export const npm_package_scripts_postinstall: string;
	export const FZF_DEFAULT_OPTS: string;
	export const npm_config_registry: string;
	export const npm_package_repository_directory: string;
	export const npm_node_execpath: string;
	export const LC_NUMERIC: string;
	export const OLDPWD: string;
	export const GOPATH: string;
	export const npm_package_types: string;
	export const npm_package_engines_node: string;
	export const TERM_PROGRAM: string;
}

/**
 * Similar to [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		SHELL: string;
		npm_command: string;
		LSCOLORS: string;
		SESSION_MANAGER: string;
		USER_ZDOTDIR: string;
		QT_ACCESSIBILITY: string;
		COLORTERM: string;
		PYENV_SHELL: string;
		npm_package_scripts_generate_types: string;
		XDG_CONFIG_DIRS: string;
		npm_package_devDependencies__types_node: string;
		LESS: string;
		XDG_SESSION_PATH: string;
		XDG_MENU_PREFIX: string;
		npm_package_repository_url: string;
		TERM_PROGRAM_VERSION: string;
		GTK_IM_MODULE: string;
		CLUTTER_BACKEND: string;
		npm_package_exports___hooks_import: string;
		LANGUAGE: string;
		_P9K_TTY: string;
		NODE: string;
		npm_package_scripts_test_cross_platform_build: string;
		LC_ADDRESS: string;
		LC_NAME: string;
		npm_package_exports___node_polyfills_types: string;
		SSH_AUTH_SOCK: string;
		npm_package_devDependencies_dts_buddy: string;
		P9K_TTY: string;
		NODENV_DIR: string;
		XMODIFIERS: string;
		npm_package_peerDependencies_svelte: string;
		DESKTOP_SESSION: string;
		LC_MONETARY: string;
		SSH_AGENT_PID: string;
		NODENV_VERSION: string;
		npm_package_exports___import: string;
		EDITOR: string;
		npm_package_scripts_test_unit: string;
		FZF_ALT_C_OPTS: string;
		GOENV_SHELL: string;
		GTK_MODULES: string;
		XDG_SEAT: string;
		npm_package_dependencies_sade: string;
		PWD: string;
		npm_package_devDependencies_vite: string;
		XDG_SESSION_DESKTOP: string;
		LOGNAME: string;
		QT_QPA_PLATFORMTHEME: string;
		XDG_SESSION_TYPE: string;
		PANEL_GDK_CORE_DEVICE_EVENTS: string;
		PNPM_HOME: string;
		XAUTHORITY: string;
		npm_package_exports___node_import: string;
		npm_package_dependencies_cookie: string;
		FZF_DEFAULT_COMMAND: string;
		VSCODE_GIT_ASKPASS_NODE: string;
		npm_package_dependencies_sirv: string;
		npm_package_dependencies_tiny_glob: string;
		XDG_GREETER_DATA_DIR: string;
		npm_package_bugs_url: string;
		npm_package_exports___node_types: string;
		npm_package_exports___vite_types: string;
		VSCODE_INJECTION: string;
		GDM_LANG: string;
		NODENV_SHELL: string;
		HOME: string;
		NODENV_ORIG_PATH: string;
		LC_PAPER: string;
		LANG: string;
		npm_package_devDependencies_typescript: string;
		LS_COLORS: string;
		FZF_CTRL_R_OPTS: string;
		XDG_CURRENT_DESKTOP: string;
		NODENV_ROOT: string;
		npm_package_version: string;
		VIRTUAL_ENV: string;
		npm_package_files_0: string;
		npm_package_scripts_check_all: string;
		npm_package_files_1: string;
		npm_package_files_2: string;
		npm_package_repository_type: string;
		npm_package_files_3: string;
		npm_package_files_4: string;
		npm_package_files_5: string;
		npm_package_files_6: string;
		npm_package_scripts_test_integration: string;
		GIT_ASKPASS: string;
		npm_package_exports___vite_import: string;
		XDG_SEAT_PATH: string;
		npm_package_peerDependencies__sveltejs_vite_plugin_svelte: string;
		npm_package_devDependencies__types_set_cookie_parser: string;
		npm_package_dependencies_kleur: string;
		GOROOT: string;
		NODENV_HOOK_PATH: string;
		npm_package_devDependencies_rollup: string;
		INIT_CWD: string;
		CHROME_DESKTOP: string;
		CLUTTER_IM_MODULE: string;
		npm_package_scripts_test_cross_platform_dev: string;
		npm_package_scripts_format: string;
		npm_package_dependencies_import_meta_resolve: string;
		npm_lifecycle_script: string;
		npm_package_description: string;
		VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
		npm_package_devDependencies__sveltejs_vite_plugin_svelte: string;
		XDG_SESSION_CLASS: string;
		npm_package_peerDependencies_vite: string;
		LC_IDENTIFICATION: string;
		TERM: string;
		npm_package_name: string;
		ZSH: string;
		FZF_CTRL_T_COMMAND: string;
		VSCODE_NONCE: string;
		ZDOTDIR: string;
		npm_package_type: string;
		USER: string;
		npm_config_frozen_lockfile: string;
		npm_package_devDependencies_vitest: string;
		npm_package_exports___types: string;
		FZF_ALT_C_COMMAND: string;
		VSCODE_GIT_IPC_HANDLE: string;
		npm_package_exports___package_json: string;
		npm_package_homepage: string;
		FZF_CTRL_T_OPTS: string;
		npm_package_dependencies_set_cookie_parser: string;
		npm_package_dependencies__types_cookie: string;
		DISPLAY: string;
		npm_package_exports___node_polyfills_import: string;
		npm_lifecycle_event: string;
		SHLVL: string;
		npm_package_dependencies_magic_string: string;
		PAGER: string;
		LC_TELEPHONE: string;
		GOENV_ROOT: string;
		QT_IM_MODULE: string;
		LC_MEASUREMENT: string;
		_P9K_SSH_TTY: string;
		XDG_VTNR: string;
		npm_package_devDependencies__types_connect: string;
		XDG_SESSION_ID: string;
		PAPERSIZE: string;
		VIRTUAL_ENV_PROMPT: string;
		npm_config_user_agent: string;
		npm_package_dependencies_mrmime: string;
		npm_package_scripts_lint: string;
		PNPM_SCRIPT_SRC_DIR: string;
		npm_execpath: string;
		npm_package_devDependencies_svelte: string;
		npm_package_scripts_test: string;
		XDG_RUNTIME_DIR: string;
		npm_package_devDependencies_svelte_preprocess: string;
		COMPIZ_CONFIG_PROFILE: string;
		npm_package_scripts_generate_version: string;
		PYENV_ROOT: string;
		LC_TIME: string;
		npm_package_dependencies_esm_env: string;
		npm_package_keywords_4: string;
		P9K_SSH: string;
		npm_package_keywords_1: string;
		npm_package_keywords_0: string;
		npm_package_keywords_3: string;
		npm_package_keywords_2: string;
		npm_package_bin_svelte_kit: string;
		VSCODE_GIT_ASKPASS_MAIN: string;
		GTK3_MODULES: string;
		XDG_DATA_DIRS: string;
		npm_package_scripts_check: string;
		GDK_BACKEND: string;
		PATH: string;
		npm_package_dependencies_devalue: string;
		GDMSESSION: string;
		npm_package_exports___hooks_types: string;
		ORIGINAL_XDG_CURRENT_DESKTOP: string;
		npm_package_devDependencies__playwright_test: string;
		DBUS_SESSION_BUS_ADDRESS: string;
		npm_package_license: string;
		npm_package_scripts_postinstall: string;
		FZF_DEFAULT_OPTS: string;
		npm_config_registry: string;
		npm_package_repository_directory: string;
		npm_node_execpath: string;
		LC_NUMERIC: string;
		OLDPWD: string;
		GOPATH: string;
		npm_package_types: string;
		npm_package_engines_node: string;
		TERM_PROGRAM: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
