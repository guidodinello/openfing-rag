type RawCredentials = {
  email: string;
  password: string;
};

type Credentials = {
  email: string;
  password: string;
};

type IUserContext = {
  user: User | null;
  isLogged: boolean;
  login: (credentials: Credentials) => Promise<User>;
  logout: () => Promise;
};
