import React from 'react';

// يجب أن تتطابق هذه الواجهة مع واجهة User في ملف الخدمة (userService.ts)
interface User {
  id: number;
  username: string;
  email: string;
}

// تعريف الخصائص (Props) التي يستقبلها المكون
interface UsersListProps {
  users: User[];
  isLoading: boolean;
  error: string | null;
}

const UsersList: React.FC<UsersListProps> = ({ users, isLoading, error }) => {
  if (isLoading) {
    return <p>جاري تحميل البيانات...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>حدث خطأ: {error}</p>;
  }

  if (users.length === 0) {
    return <p>لا يوجد مستخدمون لعرضهم.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>اسم المستخدم</th>
          <th>البريد الإلكتروني</th>
        </tr>
      </thead>
      <tbody>
        {users.map((user) => (
          <tr key={user.id}>
            <td>{user.username}</td>
            <td>{user.email}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default UsersList;