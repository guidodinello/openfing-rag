import { API_ROUTES } from "networking/api-routes";
import { ApiService } from "networking/api-service";
import { AuthSerializer } from "networking/serializers/auth-serializer";

export class GenerativeController {
  static async(prompt: Prompt): Promise<String> {
    const serializedCredentials = AuthSerializer.serialize(prompt);

    const response = await ApiService.post<Message>(
      API_ROUTES.AUTH.LOGIN,
      serializedCredentials
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
