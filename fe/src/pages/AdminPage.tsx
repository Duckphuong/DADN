import React, {useEffect, useState } from 'react';
import { userService } from '../services/api';
import { authService } from '../services/authService';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { 
  Plus, 
  Search, 
  Edit2, 
  Trash2, 
  ShieldAlert, 
  UserCircle 
} from 'lucide-react';

interface User {
  id: string;
  fullName: string;
  email: string;
  role: 'ADMIN' | 'MANAGER' | 'USER';
  status: 'ACTIVE' | 'INACTIVE';
  phoneNumber?: string;
  urlAvatar?: string;
  lastActive?: string;
}

export function Admin() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true); 

  const [searchQuery, setSearchQuery] = useState('');

  // Dialog states
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  
  // Dialog Error
  const [emailError, setEmailError] = useState("");
  const [nameError, setNameError] = useState("");

  // Form states
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phoneNumber: '',
    role: 'MANAGER' as User['role'],
    status: 'ACTIVE' as User['status'],
  });

  const filteredUsers = users.filter(user => 
    user.fullName.toLowerCase().includes(searchQuery.toLowerCase()) || 
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const data = await userService.getAllUsers();
      setUsers(data);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      alert("Something went wrong. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await userService.deleteUser(id);
        setUsers(users.filter(u => u.id !== id));
        alert("User deleted successfully.");
      } catch (error) {
        console.error("Delete error:", error);
        alert("Failed to delete user.");
      }
    }
  };

  const handleOpenDialog = async (user?: User) => {
    setNameError("");
    setEmailError("");
    
    if (user) {
      try {
        // Gọi API để lấy thông tin chi tiết nhất của User trước khi edit
        const latestUserData = await userService.getUserById(user.id);
        setEditingUser(latestUserData);
        setFormData({
          fullName: latestUserData.fullName,
          email: latestUserData.email,
          phoneNumber: latestUserData.phoneNumber || '',
          role: latestUserData.role,
          status: latestUserData.status,
        });
      } catch (error) {
        alert("Could not fetch user details.");
        return;
      }
    } else {
      // Logic cho Create New User
      setEditingUser(null);
      setFormData({
        fullName: '',
        email: '',
        phoneNumber: '',
        role: 'MANAGER',
        status: 'ACTIVE',
      });
    }
    setIsDialogOpen(true);
  };

  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        // TRƯỜNG HỢP UPDATE
        const updatedUser = await userService.updateUser(editingUser.id, {
          fullName: formData.fullName,
          phoneNumber: formData.phoneNumber,
          role: formData.role,
          status: formData.status,
        });
        
        setUsers(users.map(u => u.id === editingUser.id ? { ...u, ...updatedUser } : u));
        alert("User updated successfully!");
      } else {
        // TRƯỜNG HỢP CREATE NEW (Sử dụng register)
        const resultRole = await authService.register({
          fullName: formData.fullName,
          email: formData.email,
          phoneNumber: formData.phoneNumber,
          role: formData.role,
          status: formData.status,
          password: "123"
        });

        if (resultRole) {
          alert("User created successfully!");
          fetchUsers();
        } else {
          alert("Failed to create user.");
        }
      }
      setIsDialogOpen(false);
    } catch (error) {
      console.error("Save error:", error);
      alert("An error occurred while saving.");
    }
  };

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const validateEmail = (email: string) => {
    if (email && !emailRegex.test(email)) {
      setEmailError('Invalid email.');
      return false;
    }
    setEmailError("");
    return true;
  };
  
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData({ ...formData, fullName: value });
    
    if (nameError) {
      if (value.trim() !== "") {
        setNameError("");
      } else {
        setNameError("Full Name is required.");
      }
    }
  };
  
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData({ ...formData, email: value });
    if (emailError) validateEmail(value);
  };

  const onSave = () => {
    const isNameValid = formData.fullName.trim() !== "";
    const isEmailValid = validateEmail(formData.email);

    if (!isNameValid) {
      setNameError("Full Name is required.");
    } else {
      setNameError("");
    }

    if (!isNameValid || !isEmailValid) {
      return;
    }

    setNameError("");
    setEmailError("");
    handleSaveUser();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-blue-100 flex flex-col">
      <Header />
      
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-row justify-between items-center gap-4">
          <div>
            <h2 className="text-cyan-900 text-3xl font-bold flex items-center gap-3">
              <ShieldAlert className="w-8 h-8 text-cyan-900" />
              User Management
            </h2>
            <p className="text-slate-600 mt-1">Manage system access, roles, and permissions.</p>
          </div>
          
          <Button 
            onClick={() => handleOpenDialog()} 
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-xl flex items-center shadow-md shrink-0"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add New User
          </Button>
        </div>

        <div className="bg-white/80 backdrop-blur-xl border border-white/40 shadow-xl rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-100">
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <Search className="w-5 h-5 text-slate-400" />
              </div>
              <Input 
                placeholder="Search users by name or email..." 
                className="w-full h-12 bg-white border-slate-200 rounded-2xl focus:border-slate-400"
                style={{ paddingLeft: '2.5rem' }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50/80">
                  <TableHead className="text-center font-bold">User</TableHead>
                  <TableHead className="text-center font-bold">Role</TableHead>
                  <TableHead className="text-center font-bold">Status</TableHead>
                  <TableHead className="text-center font-bold">Last Active</TableHead>
                  <TableHead className="text-center font-bold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                      No users found matching "{searchQuery}"
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((user) => (
                    <TableRow key={user.id} className="hover:bg-slate-50/50">
                      <TableCell>
                        <div className="flex items-center gap-4 ml-5">
                          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700">
                            <UserCircle className="w-6 h-6" />
                          </div>
                          <div>
                            <div className="font-medium text-slate-900">{user.fullName}</div>
                            <div className="text-sm text-slate-500">{user.email}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {(() => {
                          const styles = {
                            ADMIN: { backgroundColor: '#f3e8ff', color: '#7e22ce', border: '1px solid #e9d5ff' },
                            MANAGER: { backgroundColor: '#dbeafe', color: '#1d4ed8', border: '1px solid #bfdbfe' },
                            USER: { backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' },
                          };
                          const currentStyle = styles[user.role] || styles.USER;
                          return (
                            <Badge
                              style={currentStyle}
                              className="px-2 py-1 rounded-md font-medium shadow-none rounded-xl"
                            >
                              {user.role}
                            </Badge>
                          );
                        })()}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary" className={
                          user.status === 'ACTIVE' 
                            ? 'bg-green-100 text-green-700 hover:bg-green-100 py-1 rounded-xl border-xl border-green-200' 
                            : 'bg-slate-100 text-slate-700 hover:bg-slate-100 py-1 rounded-xl border-xl border-slate-200'
                        }>
                          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${user.status === 'ACTIVE' ? 'bg-green-500' : 'bg-slate-400'}`}></span>
                          {user.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center text-slate-500 text-sm">
                        {user.lastActive}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex justify-center gap-3">
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleOpenDialog(user)}
                            title="Edit"
                            className="text-slate-500 hover:text-blue-600 hover:bg-blue-100"
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleDeleteUser(user.id)}
                            title="Remove"
                            className="text-slate-500 hover:text-red-600 hover:bg-red-100"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </main>

      <Footer />

      {/* User Form Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent 
          className="bg-white text-slate-900 shadow-2xl border border-slate-200 rounded-2xl sm:max-w-[768px] w-[95vw]"
        >
          <DialogHeader>
            <DialogTitle>{editingUser ? 'Edit User' : 'Add New User'}</DialogTitle>
            <DialogDescription>
              {editingUser 
                ? "Update the user's details and permissions here." 
                : "Create a new user account to grant access to the dashboard."}
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Full Name</Label>
              <Input 
                id="name"
                className={`rounded-lg ${nameError ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
                value={formData.fullName}
                // onChange={e => setFormData({...formData, name: e.target.value})}
                onChange={handleNameChange}
                placeholder="e.g. Jane Doe"
              />
              {nameError && <span className="text-sm text-red-500">{nameError}</span>}
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="email">Email Address</Label>
              <Input 
                id="email" 
                type="email"
                className={`rounded-lg ${emailError ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
                value={formData.email}
                onChange={handleEmailChange}
                onBlur={() => validateEmail(formData.email)}
                placeholder="e.g. jane@gmail.com"
              />
              {emailError && <span className="text-sm text-red-500">{emailError}</span>}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="phoneNumber">Phone Number</Label>
              <Input 
                id="phoneNumber" 
                type="phoneNumber"
                className={`rounded-lg`}
                value={formData.phoneNumber}
                onChange={e => setFormData({...formData, phoneNumber: e.target.value})}
                onBlur={() => validateEmail(formData.phoneNumber)}
                placeholder="e.g. 1234567890"
              />
              {/* {emailError && <span className="text-sm text-red-500">{emailError}</span>} */}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="role">Role</Label>
                <select 
                  id="role"
                  className="rounded-lg flex h-10 w-full items-center justify-between rounded-md border border-input bg-input-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground 
                            focus:outline-none focus:border-ring focus:ring-ring/50 focus-visible:ring-[1px] 
                            disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.role}
                  onChange={e => setFormData({...formData, role: e.target.value as User['role']})}
                >
                  <option value="ADMIN">Admin</option>
                  {/* <option value="MANAGER">Manager</option> */}
                  <option value="USER">User</option>
                </select>
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <select 
                  id="status"
                  className="rounded-lg flex h-10 w-full items-center justify-between rounded-md border border-input bg-input-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground 
                            focus:outline-none focus:border-ring focus:ring-ring/50 focus-visible:ring-[1px] 
                            disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.status}
                  onChange={e => setFormData({...formData, status: e.target.value as User['status']})}
                >
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>
            </div>
          </div>
          
          <DialogFooter className="flex flex-row justify-end gap-3 mt-6">
            <Button 
              variant="outline" 
              type="button"
              onClick={() => setIsDialogOpen(false)}
              className="rounded-xl px-6 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              Cancel
            </Button>
            <Button 
              variant="outline" 
              type="button"x
              onClick={onSave} 
              className="rounded-xl px-6 bg-blue-600 text-white hover:bg-blue-700 hover:text-white transition-colors"
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
