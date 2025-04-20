import { API_ROUTES } from "networking/api-routes";
import { ApiService } from "networking/api-service";
import { AuthSerializer } from "networking/serializers/auth-serializer";

class AuthController {
    static async login(credentials: Credentials): Promise<User> {
        const serializedCredentials = AuthSerializer.serialize(credentials);

        const response = await ApiService.post<RawUser>(
            API_ROUTES.AUTH.LOGIN,
            serializedCredentials,
        );

        if (typeof response.data.error !== "undefined")
            throw new Error(response.data.error);

        return AuthSerializer.deSerialize(response.data);
    }

    static async logout(): Promise<boolean> {
        const response = await ApiService.post(API_ROUTES.AUTH.LOGOUT);

        return response.status === 200;
    }
}

export { AuthController };
