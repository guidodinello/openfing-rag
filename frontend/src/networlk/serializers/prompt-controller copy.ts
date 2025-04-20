class AuthSerializer {
  static deSerialize(data: RawUser): User {
    return {
      id: data.id,
      email: data.email,
      createdAt: new Date(data.created_at),
    };
  }

  static serialize(credentials: Credentials): RawCredentials {
    return {
      email: credentials.email,
      password: credentials.password,
    };
  }
}

export { AuthSerializer };
